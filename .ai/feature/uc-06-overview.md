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
- W `MVP` `BE` rozwiązuje je po swojej stronie na podstawie własnej polityki oraz `TrainingDefaults.*` z `appsettings.{environment}.json`.
- `TrainingDefaults.DefaultTrainingProfileName` wskazuje domyślny preset parametrów treningu dla nowego runu.
- `TrainingDefaults.DefaultAugmentationProfileName` wskazuje domyślny preset augmentacji dla nowego runu.
- `TrainingDefaults.DefaultBenchmarkName` wskazuje benchmark używany do końcowej ewaluacji.
- `TrainingDefaults.DefaultSeed` wskazuje domyślny seed runu.

### `snapshot` i `sequence`
- `snapshot` jest jednorazowym zrzutem bieżącego stanu runu wysyłanym przez `BE` zaraz po zestawieniu albo odtworzeniu kanału `SignalR`.
- `snapshot` nie jest komendą sterującą runem i nie pochodzi bezpośrednio z `ML`.
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
- Jeśli aktywny run już istnieje, `BE` zwraca `409 training_run_already_active`.
- Po takim `409` klient nie zgaduje `runName`, tylko pobiera aktywny run przez `GET /api/trainings/active`.
- Po zakończeniu albo anulowaniu aktywnego runu można uruchomić kolejny.

## Publiczne eventy `BE -> FE`
- `snapshot`
  - generowany wyłącznie przez `BE` po zestawieniu kanału,
  - nie pochodzi bezpośrednio z `ML`,
  - dla aktywnego runu niesie bieżący `status`, `stage` i `progress`, a `result = null` i `failure = null`.
- `statusChanged`
  - zmiana stanu workflow w trakcie aktywnego runu; `result = null`, `failure = null`.
- `progress`
  - aktualizacja postępu; zwykle `status = running`, a `result = null` i `failure = null`.
- `completed`
  - sukces runu; `status = succeeded`, `result != null`, `failure = null`.
- `failed`
  - błąd techniczny albo crash po uruchomieniu runu; `status = failed`, `result = null`, `failure != null`.
- `cancelled`
  - run przerwany na żądanie użytkownika; publiczny event jest publikowany po cleanupie artefaktów runtime, z `status = cancelled`, `result = null`, `failure = null`.

## Wewnętrzne eventy `ML -> BE`
- `statusChanged`
- `progress`
- `completed`
- `failed`
- `cancelled`
- `ML` nie wysyła eventu `snapshot`.

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
12. Jeśli aktywnego runu nie ma, `BE` generuje `runName` i `producedModelName`.
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
25. Po zdarzeniu końcowym `cancelled` `BE` zachowuje `trainings/metadata/{runName}.json` ze statusem `cancelled`, usuwa artefakty runtime runu z `trainings/runs/{runName}`, `trainings/reports/{runName}`, katalogu tymczasowego oraz częściowo utworzonego katalogu `models/registry/{producedModelName}`, a dopiero potem publikuje publiczny event `cancelled`.
26. Run staje się widoczny w późniejszych use case'ach:
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
- Jeśli żądanie nie powoduje nowej zmiany stanu, `202 Accepted` oznacza przyjęcie żądania typu no-op, a bieżący stan runu klient odzyskuje później przez `GET /api/trainings/active` albo kanał `SignalR`.

## Statusy runu
### Statusy aktywne
- `queued`
- `starting`
- `running`
- `cancelling`

### Statusy końcowe
- `succeeded`
- `failed`
- `cancelled`

## Wartości `stage`
- `stage` jest grubą fazą techniczną runu i nie zastępuje pola `status`.
- W MVP dopuszczalne wartości to:
  - `queued`
  - `training`
  - `evaluation`
  - `finished`
- `status` opisuje stan workflow, a `stage` opisuje bieżącą fazę techniczną pracy.
- `starting` jest stanem przejściowym po zapisaniu rekordu runu i przed otrzymaniem `202 Accepted` z `ML`.
- Jeśli start nie powiedzie się jeszcze w tym oknie synchronicznym, `BE` robi rollback i nie pozostawia trwałego aktywnego runu w statusie `starting`.

## Rozwiązywanie konfiguracji runu
- W `MVP` `FE` wysyła tylko `baseModelName` i `processedDatasetName`.
- `BE` rozwiązuje `trainingMode`, `trainingProfileName`, `augmentationProfileName`, `benchmarkName` i `seed` na podstawie własnej polityki oraz `TrainingDefaults.*` z `appsettings.{environment}.json`.
- W `local` wartości pochodzą z `appsettings.local.json`, a w `production` z `appsettings.production.json` przygotowanego przez workflow.
- W `MVP` `BE` przypisuje `trainingMode = fineTuning`; to nie jest parametr wejściowy z `FE`.
- W `MVP` `trainingProfileName` i `augmentationProfileName` nie są dziedziczone z modelu bazowego i nie są jeszcze podawane przez użytkownika.
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

### Co zapisuje `ML`
- `trainings/runs/{runName}`
- `trainings/reports/{runName}`
- `models/registry/{producedModelName}/artifacts` wyłącznie dla runu zakończonego sukcesem
- Przy `cancelled` artefakty runtime runu są usuwane, ale `trainings/metadata/{runName}.json` pozostaje zachowane po stronie `BE`.

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

## Najważniejsze zasady architektoniczne
- `FE` wybiera tylko nazwy logiczne, nigdy ścieżki systemowe.
- `BE` jest właścicielem workflow, statusów i rekordów systemowych.
- `ML` wykonuje pracę techniczną i raportuje do `BE`.
- `runName` identyfikuje proces treningowy, nie model.
- Model bootstrap może nie mieć `runName`.
- System nie buduje kolejki runów.
- `snapshot` jest eventem publicznym generowanym przez `BE`, a nie eventem technicznym z `ML`.
- Utrata kanału `SignalR` nie zatrzymuje treningu.
