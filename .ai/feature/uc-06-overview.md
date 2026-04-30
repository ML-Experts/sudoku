```mermaid
flowchart TD
    A[FE: otwiera ekran treningu] -->|FE -> BE<br/>GET /api/trainings/active| B[BE: sprawdza aktywny run<br/>read trainings/metadata/*.json]

    B --> C{Aktywny run istnieje?}

    C -->|200 OK| D[FE: dostaje aktywny run]
    D -->|FE -> BE<br/>SignalR /ws/trainings/{runName}| E[FE: odtwarza monitoring]

    C -->|204 No Content| F[FE: pobiera modele bazowe]
    F -->|FE -> BE<br/>GET /api/models/registry| G[BE: listuje modele z registry<br/>read models/registry/*/model.json]

    G --> H[FE: pobiera gotowe datasety]
    H -->|FE -> BE<br/>GET /api/datasets/processed| I[BE: listuje przetworzone datasety<br/>read data/processed/*.npz]

    I --> J[FE: użytkownik wybiera model i dataset]

    J -->|FE -> BE<br/>POST /api/trainings| K[BE: waliduje start runu<br/>read models/registry/{baseModelName}/model.json<br/>read data/processed/{processedDatasetName}.npz]

    K --> L{Walidacja OK?}

    L -->|nie<br/>400 / 404 / 409| M[FE: pokazuje błąd walidacji]

    L -->|tak| N[BE: rezerwuje runName i tworzy rekord runu<br/>create trainings/metadata/{runName}.json<br/>status: starting/queued]

    N -->|BE -> ML<br/>POST /ml/trainings| O[ML API: waliduje i przyjmuje zlecenie startu]

    O --> P{ML API przyjęło zlecenie?}

    P -->|nie<br/>4xx / 5xx / timeout| Q[BE: mapuje błąd ML<br/>update trainings/metadata/{runName}.json<br/>status: failed albo cleanup startu]
    Q -->|BE -> FE<br/>4xx / 5xx albo 503 / 504| R[FE: pokazuje błąd startu]

    P -->|tak<br/>202 Accepted| S[BE: zwraca uruchomiony run<br/>update trainings/metadata/{runName}.json<br/>status: queued]
    S -->|BE -> FE<br/>202 TrainingRunApiResponse| T[FE: przechodzi do monitoringu]
    T -->|FE -> BE<br/>SignalR /ws/trainings/{runName}| U[FE: monitoruje postęp]

    O --> V[ML worker: wykonuje trening w tle<br/>write tmp/trainings/{runName}/...<br/>write trainings/runs/{runName}/...]

    V --> VA[ML worker: zapisuje artefakty i raport<br/>write models/registry/{producedModelName}/artifacts/model.keras<br/>write trainings/reports/{runName}/...]

    VA -->|ML -> BE<br/>POST /internal/ml/trainings/{runName}/events| W[BE: zapisuje event i aktualizuje status<br/>update trainings/metadata/{runName}.json]

    W -->|BE -> FE<br/>SignalR event| U

    W --> X{Czy event kończy run?}

    X -->|nie<br/>progress / statusChanged| V

    X -->|tak<br/>completed| Y[BE: finalizuje model wynikowy<br/>create models/registry/{producedModelName}/model.json<br/>update trainings/metadata/{runName}.json<br/>status: succeeded]

    X -->|tak<br/>failed| Z[BE: oznacza run jako failed<br/>update trainings/metadata/{runName}.json<br/>delete trainings/runs/{runName}/...<br/>delete tmp/trainings/{runName}/...]

    X -->|tak<br/>cancelled| AA[BE: oznacza run jako cancelled<br/>update trainings/metadata/{runName}.json<br/>delete trainings/runs/{runName}/...<br/>delete tmp/trainings/{runName}/...]

    U --> AB{Użytkownik anuluje?}

    AB -->|tak| AC[FE: zleca anulowanie]
    AC -->|FE -> BE<br/>POST /api/trainings/{runName}/cancel| AD[BE: przyjmuje cancel<br/>update trainings/metadata/{runName}.json<br/>status: cancelling]

    AD -->|BE -> ML<br/>POST /ml/trainings/{runName}/cancel| AE[ML API: przyjmuje zlecenie anulowania]
    AE -->|ML -> BE<br/>POST /internal/ml/trainings/{runName}/events<br/>event: cancelled| W

    AB -->|nie| V

    %% FE -> BE
    linkStyle 0,3,5,7,9,19,31 stroke:#2563eb,stroke-width:2px

    %% BE -> FE / SignalR / HTTP response to FE
    linkStyle 2,4,16,18,23 stroke:#16a34a,stroke-width:2px

    %% BE -> ML
    linkStyle 13,32 stroke:#ea580c,stroke-width:2px

    %% ML -> BE
    linkStyle 22,33 stroke:#ca8a04,stroke-width:2px

    %% Internal decisions / local workflow
    linkStyle 1,6,8,10,11,12,14,15,17,20,21,24,25,26,27,28,29,30,34 stroke:#7c3aed,stroke-width:1.5px
```
# UC-06 — Przepływ End-to-End

## Cel dokumentu
- Zebrać w jednym miejscu pełny przebieg `UC-06` ponad podziałem na `FE`, `BE` i `ML`.
- Wyjaśnić relację `runName` -> rekord runu -> model wynikowy.
- Ustalić jeden spójny kontrakt dla startu, odzyskania aktywnego runu, anulowania, postępu i zakończenia.

## Główne pojęcia
### `runName`
- `runName` jest identyfikatorem jednego konkretnego procesu treningowego.
- To nie jest identyfikator modelu, tylko identyfikator runu.
- `runName` spina:
  - publiczne API `POST /api/trainings`, `GET /api/trainings/active`, później `GET /api/trainings/{runName}`,
  - kanał postępu `SignalR /ws/trainings/{runName}`,
  - rekord `trainings/metadata/{runName}.json`,
  - katalog `trainings/runs/{runName}`,
  - katalog `trainings/reports/{runName}`.

### `producedModelName`
- `producedModelName` jest logiczną nazwą modelu wynikowego, który powstaje po zakończeniu runu.
- W MVP może być równe `runName`, ale semantycznie to nie jest to samo.

### Model bootstrap
- Model bootstrap to wpis ręcznie dodany do `models/registry/{modelName}`.
- Taki model:
  - ma własny `model.json`,
  - ma własne `artifacts/`,
  - może mieć `canStartTraining = true`,
  - nie musi mieć żadnego rekordu w `trainings/*`,
  - ma `sourceType = bootstrap` i `sourceRunName = null`.
- Nie potrzebuje własnego `runName`, bo nie powstał w wyniku runu uruchomionego przez system.

### Profile treningowe i augmentacyjne
- `trainingMode` opisuje typ uruchamianego runu; w `MVP` jest to `fineTuning`.
- `trainingProfileName` identyfikuje preset parametrów treningu, np. liczbę epok, batch size, learning rate albo politykę zamrażania warstw.
- `augmentationProfileName` identyfikuje preset augmentacji danych używany podczas treningu.
- `benchmarkName` identyfikuje wspólny benchmark używany do końcowego porównania modeli.
- `seed` jest ziarnem losowości runu potrzebnym do powtarzalności eksperymentu.
- W `MVP` profile i pozostała resolved konfiguracja runu nie są dziedziczone z modelu bazowego i nie są podawane przez użytkownika.
- W `MVP` system wspiera dokładnie jeden preset treningowy i dokładnie jeden preset augmentacji po stronie `BE`.
- `FE` nie pobiera katalogu presetów i nie przekazuje żadnych identyfikatorów presetów w `POST /api/trainings`.
- W `MVP` `BE` rozwiązuje je po swojej stronie na podstawie własnej polityki oraz `TrainingDefaults.*` z `appsettings.{environment}.json`.
- `TrainingDefaults.DefaultTrainingProfileName` wskazuje domyślny preset parametrów treningu dla nowego runu.
- `TrainingDefaults.DefaultAugmentationProfileName` wskazuje domyślny preset augmentacji dla nowego runu.
- `TrainingDefaults.DefaultBenchmarkName` wskazuje benchmark używany do końcowej ewaluacji.
- `TrainingDefaults.DefaultSeed` wskazuje domyślny seed runu.

### `snapshot` i `sequence`
- `snapshot` jest jednorazowym zrzutem bieżącego stanu runu wysyłanym przez `BE` zaraz po zestawieniu albo odtworzeniu kanału `SignalR`.
- `snapshot` nie jest komendą sterującą runem i nie pochodzi bezpośrednio z `ML`.
- `snapshot` opisuje aktualny publiczny stan runu znany przez `BE`, a nie surowo ostatni event techniczny otrzymany z `ML`.
- Jeśli run nie wszedł jeszcze w realne wykonywanie po stronie `ML`, `snapshot` może zwrócić stabilny stan `queued`.
- Jeśli run zdążył się już zakończyć przed zestawieniem albo odtworzeniem kanału, `snapshot` może być terminalny i nieść ten sam stan publiczny, który `BE` pokazałby w końcowym evencie.
- Po dostarczeniu terminalnego `snapshot` `BE` nie ma obowiązku utrzymywania kanału otwartego dłużej niż potrzeba do wysłania tego jednego komunikatu.
- `sequence` jest rosnącym numerem porządkowym stanu w obrębie jednego runu.
- `snapshot.sequence` jest równe ostatniej sekwencji zaakceptowanej przez `BE` w momencie wygenerowania `snapshot`.
- `FE` może ignorować spóźnione eventy o niższym `sequence`, aby nie cofać UI do starszego stanu.
- `FE` nie czeka na brakujące numery sekwencji; renderuje najświeższy dostępny stan.

### `reportStatus` i referencje do artefaktów
- `reportStatus` opisuje stan raportu końcowego niezależnie od statusu samego runu.
- W rekordzie `trainings/metadata/{runName}.json` dopuszczalne wartości w `MVP` to:
  - `pending` — raport nie został jeszcze wygenerowany albo run jeszcze trwa,
  - `ready` — raport został wygenerowany i jest kompletny,
  - `missing` — raport miał istnieć, ale go brakuje,
  - `corrupted` — raport istnieje, ale jest niekompletny albo uszkodzony.
- W publicznym kontrakcie `BE -> FE` pole `reportStatus` występuje wyłącznie wewnątrz `result` końcowego eventu `completed`.
- Dlatego w `UC-06` publicznie do `FE` mogą trafić tylko `ready`, `missing` albo `corrupted`.
- Podczas aktywnego runu `FE` obserwuje stan przez `status`, `stage` i `progress`; `pending` pozostaje stanem wewnętrznym rekordu runu po stronie `BE`.
- `primaryArtifactRelativePath` jest ścieżką względną względem `models/registry/{producedModelName}`.
- `summaryRelativePath`, `metricsRelativePath` i `confusionMatrixRelativePath` są ścieżkami względnymi względem `trainings/reports/{runName}`.
- Katalogi bazowe dla tych referencji są rozwiązywane przez `BE` z `appsettings.{environment}.json`; w `local` są wpisane w `appsettings.local.json`, a w `production` przygotowuje je workflow w `appsettings.production.json`.

### `requestDisposition` dla odpowiedzi `cancel`
- `CancelTrainingRunApiResponse.status` opisuje rzeczywisty bieżący stan dopasowanego runu w chwili odpowiedzi, a nie stan "wymuszony" przez samo żądanie `cancel`.
- `CancelTrainingRunApiResponse.status` może być `null`, jeśli żądanie `cancel` nie dopasowało żadnego znanego runu i serwer zwraca techniczne `202 Accepted` typu no-op.
- `CancelTrainingRunApiResponse.requestDisposition` opisuje, jak serwer obsłużył samo żądanie anulowania.
- W `MVP` dopuszczalne wartości `requestDisposition` to:
  - `cancellationRequested` — aktywny run przyjął nowe żądanie anulowania,
  - `alreadyCancelling` — run był już wcześniej w stanie `cancelling`,
  - `noopAlreadyFinished` — run był już zakończony i nowe żądanie nie zmieniło jego stanu,
  - `noopNoMatchingRun` — żądanie nie dopasowało żadnego znanego runu, ale API zachowuje uproszczone `202 Accepted`.
- `cancellationRequestedAtUtc` jest timestampem pierwszego skutecznie przyjętego żądania anulowania dla danego runu; może być `null`, jeśli run zakończył się bez przejścia przez ścieżkę anulowania albo żądanie nie dopasowało żadnego runu.

## Role warstw
### `FE`
- pokazuje listę modeli i datasetów,
- pozwala uruchomić albo wznowić monitoring aktywnego runu,
- wysyła start runu,
- monitoruje postęp przez kanał `SignalR`,
- pozwala anulować aktywny run.

### `BE`
- jest `source of truth` dla workflow i statusów,
- generuje `runName`,
- zapisuje rekord runu,
- uruchamia `ML`,
- odbiera eventy z `ML`,
- publikuje stan do `FE`,
- finalizuje `model.json` modelu wynikowego wyłącznie po sukcesie runu.

### `ML`
- wykonuje trening asynchronicznie,
- zapisuje artefakty techniczne,
- raportuje postęp i wynik do `BE`,
- nie komunikuje się bezpośrednio z `FE`,
- nie staje się drugim źródłem prawdy dla runów.

## Kanały komunikacji
### Start runu
- `FE -> BE`: `POST /api/trainings`
- `BE -> ML`: `POST /ml/trainings`

### Odtworzenie aktywnego runu
- `FE -> BE`: `GET /api/trainings/active`
- endpoint zwraca:
  - `200 OK` z `TrainingRunApiResponse`, jeśli aktywny run istnieje,
  - `204 No Content`, jeśli nie ma aktywnego runu.

### Postęp i zakończenie runu
- `ML -> BE`: `POST /internal/ml/trainings/{runName}/events`
- `BE -> FE`: `SignalR /ws/trainings/{runName}`

### Anulowanie runu
- `FE -> BE`: `POST /api/trainings/{runName}/cancel`
- `BE -> ML`: `POST /ml/trainings/{runName}/cancel`

## Autoryzacja
- Wszystkie operacje administracyjne `UC-06` używają tokenu z `UC-13`.
- Dotyczy to także kanału `SignalR /ws/trainings/{runName}`.
- Po stronie `FE` połączenie kanału postępu używa klienta `SignalR` z `accessTokenFactory`.
- `FE` nie dokleja ręcznie tokenu do URL; szczegół przekazania tokenu obsługuje biblioteka `SignalR`.
- Komunikacja `BE <-> ML` nie używa tokenu użytkownika; powinna mieć osobny mechanizm service-to-service.

## Zasada pojedynczego aktywnego runu
- System dopuszcza tylko jeden aktywny run jednocześnie.
- Aktywne statusy to:
  - `queued`
  - `starting`
  - `running`
  - `cancelling`
- System nie buduje kolejki kolejnych runów.
- Drugie kliknięcie Start nie może utworzyć nowego runu.
- Jeśli aktywny run już istnieje, `BE` zwraca publiczne `409 training_run_already_active`.
- Publiczne `409 training_run_already_active` jest zarezerwowane wyłącznie dla konfliktu z istniejącym aktywnym runem.
- Po takim `409` klient nie zgaduje `runName`, tylko pobiera aktywny run przez `GET /api/trainings/active`.
- Konflikty technicznej rezerwacji `runName` albo `producedModelName` są obsługiwane wewnętrznym retry po stronie `BE` i nie są normalnym publicznym przypadkiem `409`.
- Po zakończeniu albo anulowaniu aktywnego runu można uruchomić kolejny.

## Publiczne eventy `BE -> FE`
- `snapshot`
  - generowany wyłącznie przez `BE` po zestawieniu kanału,
  - nie pochodzi bezpośrednio z `ML`,
  - niesie aktualny publiczny stan runu znany przez `BE`,
  - dla aktywnego runu niesie bieżący `status`, `stage` i `progress`, a `result = null` i `failure = null`,
  - dla runu zakończonego może być terminalny i wtedy odzwierciedla końcowy stan publiczny: sukces z `result`, błąd z `failure` albo anulowanie bez obu tych pól.
- `statusChanged`
  - zmiana stanu workflow w trakcie aktywnego runu; `result = null`, `failure = null`.
- `progress`
  - aktualizacja postępu; zwykle `status = running`, a `result = null` i `failure = null`.
- `completed`
  - sukces runu; `status = succeeded`, `result != null`, `failure = null`.
- `failed`
  - błąd techniczny albo błąd domknięcia runu po uruchomieniu, po którym model wynikowy nie może zostać użyty do inferencji; przed publikacją eventu `BE` wykonuje cleanup artefaktów runtime analogiczny do `cancelled`; `status = failed`, `result = null`, `failure != null`.
- `cancelled`
  - run przerwany na żądanie użytkownika; publiczny event jest publikowany po cleanupie artefaktów runtime, z `status = cancelled`, `result = null`, `failure = null`.

## Wewnętrzne eventy `ML -> BE`
- `statusChanged`
- `progress`
- `completed`
- `failed`
- `cancelled`
- `ML` nie wysyła eventu `snapshot`.

## Niezawodność dostarczania eventów
- `BE -> FE` przez `SignalR` nie używa potwierdzeń aplikacyjnych `ACK` z `FE`; utrata połączenia jest odzyskiwana przez reconnect i `snapshot`.
- `ML -> BE` może powtórzyć wysyłkę tego samego eventu z tym samym `sequence`, jeśli nie otrzymało odpowiedzi `2xx` albo wystąpił timeout transportowy.
- `BE` zapisuje `lastAcceptedSequence` i traktuje event o tym samym `sequence` jako idempotentne ponowienie, a event o niższym `sequence` jako spóźniony.
- Końcowy event `completed`, `failed` albo `cancelled` musi zostać dostarczony do `BE` niezawodnie; `ML` przechowuje go jako pending i retry-uje z backoffem aż do skutecznego zapisu po stronie `BE`.
- Retry końcowego eventu nie może blokować zasobów wykonawczych treningu; po stronie `ML` trwa tylko lekki mechanizm dostarczenia finalnego stanu.

## Kanoniczne inwarianty kontraktu
- `statusChanged` i `progress` zawsze mają `result = null` oraz `failure = null`.
- `snapshot` dla aktywnego runu ma `result = null` oraz `failure = null`.
- `snapshot` dla runu zakończonego odzwierciedla końcowy stan publiczny znany przez `BE`.
- `completed` zawsze oznacza `status = succeeded`, `result != null` i `failure = null`.
- `failed` zawsze oznacza `status = failed`, `result = null` i `failure != null`.
- `cancelled` zawsze oznacza `status = cancelled`, `result = null` i `failure = null`.
- `reportStatus` może pojawić się tylko wtedy, gdy `result != null`, czyli wyłącznie w końcowym evencie `completed` albo w terminalnym `snapshot` runu zakończonego sukcesem.
- Jeśli jedynym problemem końcowym jest brakujący albo uszkodzony raport, ale artefakty modelu są kompletne i model nadaje się do inferencji, run kończy się `completed`, a nie `failed`.
- Jeśli run kończy się `failed`, oznacza to, że model wynikowy nie jest używalny do inferencji albo proces nie został poprawnie domknięty biznesowo; w takim przypadku `BE` sprząta artefakty runtime tak samo jak dla `cancelled`.
- `CancelTrainingRunApiResponse.status` zwraca bieżący stan dopasowanego runu albo `null`, jeśli nie znaleziono żadnego dopasowania, a `requestDisposition` wyjaśnia, czy żądanie anulowania było nowe, duplikatem czy no-opem.

## Przebieg end-to-end
1. Użytkownik administracyjny otwiera ekran `UC-06`.
2. `FE` najpierw pyta o stan bieżący przez `GET /api/trainings/active`.
3. Jeśli `BE` zwróci `200 OK`, `FE` przechodzi od razu do monitoringu istniejącego runu.
4. Jeśli `BE` zwróci `204 No Content`, `FE` pobiera:
   - `GET /api/models/registry`
   - `GET /api/datasets/processed`
5. `BE` składa listę modeli z `models/registry/*/model.json`.
6. `BE` składa listę datasetów z gotowych artefaktów `.npz` przygotowanych wcześniej w `UC-12`.
7. `FE` pokazuje użytkownikowi wyłącznie dane logiczne:
   - nazwę modelu,
   - typ źródła,
   - profile,
   - daty,
   - liczbę próbek.
8. Użytkownik wybiera dokładnie jeden model bazowy i dokładnie jeden dataset.
9. `FE` wysyła `POST /api/trainings` z:
   - `baseModelName`
   - `processedDatasetName`
10. `BE` sprawdza:
   - token administracyjny,
   - istnienie modelu i datasetu,
   - poprawność manifestu modelu,
   - `canStartTraining`,
   - dokładną równość `inputProfile` modelu bazowego i `preprocessingProfile` datasetu w MVP,
   - brak aktywnego runu.
11. Jeśli aktywny run już istnieje, `BE` zwraca `409 training_run_already_active`, a `FE` pobiera `GET /api/trainings/active` i przechodzi do monitoringu istniejącego runu.
12. Jeśli aktywnego runu nie ma, `BE` generuje `runName` i `producedModelName`; jeśli rezerwacja tych nazw koliduje z istniejącym stanem plikowym, `BE` wykonuje wewnętrzny retry i nie eksponuje tego przypadku jako publicznego `409`.
13. `BE` zapisuje rekord `trainings/metadata/{runName}.json` w przejściowym stanie `starting`.
14. `BE` rozwiązuje wszystkie potrzebne ścieżki absolutne na podstawie `appsettings.{environment}.json`; w `local` pochodzą z `appsettings.local.json`, a w `production` z `appsettings.production.json` przygotowanego przez workflow.
15. `BE` rozwiązuje konfigurację runu; w `MVP` przypisuje `trainingMode = fineTuning`, ustala `trainingProfileName`, `augmentationProfileName`, `benchmarkName` i `seed` po swojej stronie, a `FE` nie przekazuje tych pól w requestcie.
16. `BE` wywołuje `POST /ml/trainings`.
17. Jeśli `ML` nie przyjmie startu, zanim `BE` odpowie do `FE`, `BE` robi rollback prowizorycznego stanu: usuwa albo unieważnia rekord runu, zwalnia lock aktywnego runu i rezerwację `producedModelName`; jeśli `ML` zwróciło synchroniczny błąd walidacyjny albo kontraktowy, `BE` przepuszcza do `FE` ten sam kod i body, a dla niedostępności albo timeoutu zwraca `503` albo `504`.
18. Jeśli `ML` przyjmie run asynchronicznie i odeśle `202 Accepted`, `BE` od razu zwraca `FE` odpowiedź startową z:
   - `runName`
   - `producedModelName`
   - `status`
   - `progressChannelUrl`
19. `FE` otwiera kanał `SignalR /ws/trainings/{runName}` z tokenem przekazanym przez `accessTokenFactory`.
20. `BE` po połączeniu wysyła `snapshot` aktualnego stanu runu.
21. `ML` wykonuje trening i wysyła kolejne eventy do `BE` przez `POST /internal/ml/trainings/{runName}/events`.
22. `BE` aktualizuje własny rekord runu i dopiero wtedy publikuje ten stan do `FE`.
23. `ML` zapisuje:
   - checkpointy i logi do `trainings/runs/{runName}`,
   - raporty do `trainings/reports/{runName}`,
   - finalne artefakty modelu do `models/registry/{producedModelName}/artifacts`.
24. Po zdarzeniu końcowym `completed` `BE` finalizuje `models/registry/{producedModelName}/model.json`.
25. Jeśli końcowy problem dotyczy wyłącznie raportu (`missing` albo `corrupted`), ale artefakty modelu są kompletne, `ML` raportuje `completed`, a `BE` zachowuje model wynikowy i publikuje ostrzeżenie zamiast przechodzić do `failed`.
26. Po zdarzeniu końcowym `failed` `BE` zachowuje `trainings/metadata/{runName}.json` ze statusem `failed`, usuwa artefakty runtime runu z `trainings/runs/{runName}`, `trainings/reports/{runName}`, katalogu tymczasowego oraz częściowo utworzonego katalogu `models/registry/{producedModelName}`, a dopiero potem publikuje publiczny event `failed`.
27. Po zdarzeniu końcowym `cancelled` `BE` zachowuje `trainings/metadata/{runName}.json` ze statusem `cancelled`, usuwa artefakty runtime runu z `trainings/runs/{runName}`, `trainings/reports/{runName}`, katalogu tymczasowego oraz częściowo utworzonego katalogu `models/registry/{producedModelName}`, a dopiero potem publikuje publiczny event `cancelled`.
28. Run staje się widoczny w późniejszych use case'ach:
   - `UC-07` postęp,
   - `UC-08` lista treningów i modeli,
   - `UC-09` szczegóły i metryki,
   - `UC-10` aktywacja modelu.

## Granica z `UC-07`
- `UC-06` definiuje kontrakty startu runu, odzyskania aktywnego runu, anulowania oraz kanału postępu aktywnego runu.
- `UC-07` rozwija dedykowany widok postępu i komunikaty UI, ale nie wprowadza osobnego identyfikatora runu, osobnego transportu ani drugiego źródła statusu.
- Jeśli w `UC-07` pojawi się dodatkowy ekran, reuse'uje on te same kontrakty `GET /api/trainings/active`, `SignalR /ws/trainings/{runName}` oraz statusy zdefiniowane tutaj.

## Jak `FE` dostaje postęp bez rozmowy z `ML`
- `ML` nie rozmawia z `FE`.
- Zamiast tego:
  1. `ML` wysyła event do `BE`.
  2. `BE` zapisuje nowy stan runu.
  3. `BE` wypycha własny event do `FE`.
- Dzięki temu:
  - `BE` pozostaje właścicielem statusu,
  - `FE` ma realtime update,
  - odświeżenie strony nie gubi stanu biznesowego.

## Utrata połączenia `SignalR`
- Zerwanie kanału `SignalR` nie zatrzymuje runu.
- Run trwa dalej po stronie `ML`.
- `ML` dalej raportuje do `BE`.
- `BE` dalej aktualizuje rekord runu.
- Po reconnect `FE` powinno:
  - ponownie połączyć kanał,
  - odebrać `snapshot`,
  - jeśli nie zna już bieżącego stanu, odpytać `GET /api/trainings/active`,
  - później korzystać z `GET /api/trainings/{runName}` z `UC-09` dla widoku historycznego lub szczegółowego.

## Anulowanie runu
- Użytkownik może anulować aktywny run.
- `FE` wysyła `POST /api/trainings/{runName}/cancel`.
- `BE` przechodzi do stanu `cancelling` i wywołuje `POST /ml/trainings/{runName}/cancel`.
- `ML` ustawia własną flagę anulowania i sprawdza ją między bezpiecznymi etapami pracy.
- Po bezpiecznym przerwaniu `ML` zwalnia własne zasoby wykonawcze i wysyła event `cancelled` do `BE`.
- `BE` zachowuje `trainings/metadata/{runName}.json` ze statusem `cancelled`, usuwa artefakty runtime runu z `trainings/runs/{runName}`, `trainings/reports/{runName}`, katalogu tymczasowego oraz częściowo utworzonego katalogu `models/registry/{producedModelName}`.
- `BE` publikuje publiczny event `cancelled` dopiero po zakończeniu cleanupu.
- `cancel` jest operacją kooperacyjną i idempotentną; dla uproszczenia endpoint zawsze zwraca `202 Accepted`.
- Odpowiedź `CancelTrainingRunApiResponse` zwraca:
  - `status` równy rzeczywistemu bieżącemu statusowi dopasowanego runu albo `null`, jeśli nie znaleziono dopasowania,
  - `requestDisposition` opisujące, czy żądanie było nowe, duplikatem czy no-opem dla runu już zakończonego albo niedopasowanego.
- Jeśli żądanie nie powoduje nowej zmiany stanu, `202 Accepted` nadal oznacza przyjęcie żądania typu no-op, ale klient nie musi zgadywać wyniku, bo dostaje `status` i `requestDisposition`.

## Statusy runu
- `status` jest maszyną stanów workflow runu.
- `status` mówi, w jakim stanie biznesowym znajduje się run; nie zastępuje pola `stage`.
- Rozszerzona semantyka z tej sekcji jest kanoniczna dla `FE`, `BE` i `ML`; dokumenty warstwowe odwołują się do niej zamiast powielać pełny opis.

### Statusy aktywne
- `starting`
- `queued`
- `running`
- `cancelling`

### Znaczenie statusów aktywnych
- `starting` — `BE` zapisał rekord runu i wykonuje synchroniczny start do `ML`; to stan przejściowy używany głównie do ochrony workflow i rollbacku.
- `queued` — `ML` przyjęło start runu, ale właściwe wykonywanie nie weszło jeszcze w fazę treningu; ta nazwa nie oznacza kolejki wielu runów, tylko stan "zaakceptowany i oczekujący na wykonanie".
- `running` — run jest wykonywany; o bieżącej fazie technicznej mówi dopiero `stage`.
- `cancelling` — `BE` przyjęło żądanie anulowania i czeka na bezpieczne zatrzymanie pracy przez `ML`; to nadal status aktywny, a nie końcowy.

### Statusy końcowe
- `succeeded`
- `failed`
- `cancelled`

### Znaczenie statusów końcowych
- `succeeded` — run domknął się sukcesem; model wynikowy pozostaje używalny do inferencji, a stan raportu opisuje `reportStatus`.
- `failed` — run zakończył się błędem technicznym albo błędem domknięcia workflow; model wynikowy nie jest traktowany jako używalny do inferencji.
- `cancelled` — run został kooperacyjnie przerwany na żądanie użytkownika, a `BE` zakończył cleanup artefaktów runtime.

### Publiczna widoczność `starting`
- `starting` może istnieć w rekordzie `BE` i w krótkim oknie przejściowym workflow, ale nie jest traktowany jako pierwszy stabilny publiczny stan runu.
- Publicznie może pojawić się wyjątkowo tylko w odpowiedzi `GET /api/trainings/active`, jeśli drugi klient trafi w krótkie okno synchronicznego startu po stronie `BE`.
- Po udanym `POST /api/trainings` pierwszym stabilnym publicznym statusem zwracanym do `FE` jest `queued`.
- Kanał `SignalR /ws/trainings/{runName}` nie emituje `status = starting`; pierwszym stabilnym publicznym stanem na kanale jest `queued`.
- Jeśli start nie powiedzie się jeszcze w oknie `starting`, `BE` robi rollback i nie pozostawia trwałego aktywnego runu.

## Wartości `stage`
- `stage` jest grubą fazą techniczną runu i nie zastępuje pola `status`.
- `status` mówi, czy run trwa, kończy się albo zakończył, a `stage` mówi, na jakiej technicznej fazie pracy aktualnie jest albo był.
- Rozszerzona semantyka z tej sekcji jest kanoniczna dla wszystkich warstw.
- W MVP dopuszczalne wartości to:
  - `queued`
  - `training`
  - `evaluation`
  - `finished`

### Znaczenie wartości `stage`
- `queued` — run został zaakceptowany, ale nie wszedł jeszcze w realne wykonywanie.
- `training` — trwa właściwy trening modelu.
- `evaluation` — trwa końcowa ewaluacja, zapis raportów, benchmark lub finalizacja technicznych artefaktów modelu.
- `finished` — run został technicznie domknięty.

### Relacja `status` i `stage`
- `status = running` może występować z `stage = training` albo `evaluation`.
- `status = cancelling` zachowuje ostatnią realną fazę pracy, najczęściej `training` albo `evaluation`, aż do końcowego eventu `cancelled`.
- Dla stanów końcowych `succeeded` i `cancelled` oczekiwane `stage` to `finished`.
- Dla `failed` `stage` może pozostać ostatnią realną fazą pracy, np. `training` albo `evaluation`, aby było wiadomo, gdzie run się zatrzymał.
- `starting` jest stanem przejściowym po zapisaniu rekordu runu i przed otrzymaniem `202 Accepted` z `ML`; nie jest osobną wartością `stage`.

## Znaczenie `eventType`
- `eventType` opisuje typ komunikatu transportowego; nie jest stanem runu i nie zastępuje pól `status` ani `stage`.
- Rozszerzona semantyka z tej sekcji jest kanoniczna dla `FE`, `BE` i `ML`.

### Wartości i znaczenie
- `snapshot` — zrzut aktualnego publicznego stanu runu generowany przez `BE` po zestawieniu albo odtworzeniu kanału; nie jest wysyłany przez `ML` i może być aktywny albo terminalny.
- `statusChanged` — komunikat o zmianie stanu workflow albo istotnym przejściu technicznym, bez końcowego `result` i bez `failure`.
- `progress` — aktualizacja postępu w aktywnym runie; zwykle towarzyszy `status = running` i również nie niesie końcowego `result`.
- `completed` — końcowy sukces runu; zawsze oznacza `status = succeeded`.
- `failed` — końcowy błąd runu; zawsze oznacza `status = failed`.
- `cancelled` — końcowe anulowanie runu; zawsze oznacza `status = cancelled`.

### Relacja `eventType` do warstw
- `BE -> FE` używa publicznych eventów `snapshot`, `statusChanged`, `progress`, `completed`, `failed`, `cancelled`.
- `ML -> BE` używa eventów `statusChanged`, `progress`, `completed`, `failed`, `cancelled`.
- `ML` nie wysyła eventu `snapshot`, a `status = starting` pozostaje przejściowym stanem po stronie `BE`, widocznym publicznie co najwyżej przez `GET /api/trainings/active`, ale nie przez `SignalR`.

## Rozwiązywanie konfiguracji runu
- W `MVP` `FE` wysyła tylko `baseModelName` i `processedDatasetName`.
- `BE` rozwiązuje `trainingMode`, `trainingProfileName`, `augmentationProfileName`, `benchmarkName` i `seed` na podstawie własnej polityki oraz `TrainingDefaults.*` z `appsettings.{environment}.json`.
- W `local` wartości pochodzą z `appsettings.local.json`, a w `production` z `appsettings.production.json` przygotowanego przez workflow.
- W `MVP` `BE` przypisuje `trainingMode = fineTuning`; to nie jest parametr wejściowy z `FE`.
- W `MVP` `trainingProfileName` i `augmentationProfileName` nie są dziedziczone z modelu bazowego i nie są jeszcze podawane przez użytkownika.
- W `MVP` istnieje dokładnie jedna wspierana wartość `trainingProfileName` i dokładnie jedna wspierana wartość `augmentationProfileName`; `FE` nie wybiera ich i nie pobiera osobnego katalogu presetów.
- `trainingMode` widoczne na liście modeli opisuje istniejący wpis rejestru i jego pochodzenie, a nie konfigurację nowo uruchamianego runu.

## Reguła zgodności modelu i datasetu
- W MVP zgodność modelu bazowego z datasetem oznacza dokładną równość:
  - `RegistryModel.inputProfile`
  - `ProcessedDataset.preprocessingProfile`
- Walidację tej zgodności wykonuje `BE` przed wywołaniem `ML`.
- `ML` traktuje brak zgodności jako błąd obronny `422`, nawet jeśli `BE` powinno wychwycić taki przypadek wcześniej.

## Pliki i odpowiedzialność
### Co zapisuje `BE`
- `trainings/metadata/{runName}.json`
- finalne `models/registry/{producedModelName}/model.json` wyłącznie po `completed`
- pełną konfigurację eksperymentu, w tym `sourceRevision` ustawione w `MVP` na `null`, oraz referencje do artefaktów raportu potrzebnych później w UI
- przy `failed` i `cancelled` zachowuje rekord `trainings/metadata/{runName}.json`, ale usuwa pozostałe artefakty runtime runu oraz częściowo utworzony katalog modelu wynikowego

### Co zapisuje `ML`
- `trainings/runs/{runName}`
- `trainings/reports/{runName}`
- `models/registry/{producedModelName}/artifacts` wyłącznie dla runu zakończonego sukcesem
- Przy `failed` i `cancelled` artefakty runtime runu są usuwane przez `BE`, ale `trainings/metadata/{runName}.json` pozostaje zachowane po stronie `BE`.

## Uszkodzony raport a używalny model
- Błąd raportu nie musi oznaczać, że run jest całkowicie bezużyteczny.
- W rekordzie `BE` `reportStatus` ma pełny słownik wartości: `pending`, `ready`, `missing`, `corrupted`.
- W publicznym evencie `completed` pole `result.reportStatus` może mieć wartości `ready`, `missing` albo `corrupted`; `pending` nie jest wysyłane do `FE` w trakcie aktywnego runu.
- Jeśli finalne artefakty modelu są kompletne, ale raport jest uszkodzony albo brakujący:
  - run może zakończyć się sukcesem,
  - `reportStatus` może mieć wartość `corrupted` albo `missing`,
  - końcowy event pozostaje `completed`, a `failure` pozostaje `null`,
  - ostrzeżenie o raporcie trafia do `warnings`,
  - UI powinno pokazać ostrzeżenie o raporcie,
  - model może nadal być dostępny do aktywacji i inferencji.
- Taki przypadek nie może kończyć się eventem `failed`.

## Najważniejsze zasady architektoniczne
- `FE` wybiera tylko nazwy logiczne, nigdy ścieżki systemowe.
- `BE` jest właścicielem workflow, statusów i rekordów systemowych.
- `ML` wykonuje pracę techniczną i raportuje do `BE`.
- `runName` identyfikuje proces treningowy, nie model.
- Model bootstrap może nie mieć `runName`.
- System nie buduje kolejki runów.
- `snapshot` jest eventem publicznym generowanym przez `BE`, a nie eventem technicznym z `ML`.
- Utrata kanału `SignalR` nie zatrzymuje treningu.
