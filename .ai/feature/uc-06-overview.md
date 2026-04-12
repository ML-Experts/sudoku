# UC-06 — Przepływ End-to-End

## Cel dokumentu
- Zebrać w jednym miejscu cały przebieg `UC-06` ponad podziałem na `FE`, `BE` i `ML`.
- Wyjaśnić, czym jest `runName`, dlaczego modele bootstrap nie potrzebują własnego `runName` oraz jak przebiega komunikacja `ML -> BE -> FE`.
- Ustalić zasady pojedynczego aktywnego runu, anulowania, autoryzacji kanału postępu oraz obsługi uszkodzonego raportu.

## Główne pojęcia
### `runName`
- `runName` jest identyfikatorem jednego konkretnego procesu treningowego.
- To nie jest identyfikator modelu, tylko identyfikator runu.
- `runName` spina:
  - publiczne API `POST /api/trainings`, `GET /api/trainings/{runName}`,
  - kanał postępu `WebSocket /ws/trainings/{runName}`,
  - rekord `trainings/metadata/{runName}.json`,
  - katalog `trainings/runs/{runName}`,
  - katalog `trainings/reports/{runName}`.

### `producedModelName`
- `producedModelName` jest logiczną nazwą modelu wynikowego, który powstaje po zakończeniu runu.
- W MVP może być równe `runName`, ale semantycznie to nie jest to samo.

### Model bootstrap / seed
- Model bootstrap to wpis ręcznie dodany do `models/registry/{modelName}`.
- Taki model:
  - ma własny `model.json`,
  - ma własne `artifacts/`,
  - może mieć `canStartTraining = true`,
  - nie musi mieć żadnego rekordu w `trainings/*`,
  - ma `sourceType = bootstrap` i `sourceRunName = null`.
- Nie potrzebuje własnego `runName`, bo nie powstał w wyniku runu uruchomionego przez system.

## Role warstw
### `FE`
- pokazuje listę modeli i datasetów,
- pozwala wybrać model bazowy i dataset,
- wysyła start runu,
- monitoruje postęp przez kanał `WebSocket`,
- pozwala anulować aktywny run.

### `BE`
- jest `source of truth` dla workflow i statusów,
- generuje `runName`,
- zapisuje rekord runu,
- uruchamia `ML`,
- odbiera eventy z `ML`,
- publikuje stan do `FE`,
- finalizuje `model.json` modelu wynikowego.

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

### Postęp i zakończenie runu
- `ML -> BE`: `POST /internal/ml/trainings/{runName}/events`
- `BE -> FE`: `WebSocket /ws/trainings/{runName}`

### Anulowanie runu
- `FE -> BE`: `POST /api/trainings/{runName}/cancel`
- `BE -> ML`: `POST /ml/trainings/{runName}/cancel`

## Autoryzacja
- Wszystkie operacje administracyjne `UC-06` używają tokenu z `UC-13`.
- Dotyczy to także kanału `WebSocket /ws/trainings/{runName}`.
- Klient nie przekazuje tokenu w query string.
- Po stronie `FE` połączenie kanału postępu używa `accessTokenFactory` albo równoważnego mechanizmu.
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
- Po zakończeniu albo anulowaniu aktywnego runu można uruchomić kolejny.

## Przebieg end-to-end
1. Użytkownik administracyjny otwiera ekran `UC-06`.
2. `FE` pobiera z `BE`:
   - `GET /api/models/registry`
   - `GET /api/datasets/processed`
3. `BE` składa listę modeli z `models/registry/*/model.json`.
4. `BE` składa listę datasetów z gotowych artefaktów `.npz` przygotowanych wcześniej w `UC-12`.
5. `FE` pokazuje użytkownikowi logiczne dane:
   - nazwę modelu,
   - typ źródła,
   - profile,
   - daty,
   - liczbę próbek.
6. Użytkownik wybiera dokładnie jeden model bazowy i dokładnie jeden dataset.
7. `FE` wysyła `POST /api/trainings` z:
   - `baseModelName`
   - `processedDatasetName`
8. `BE` sprawdza:
   - token administracyjny,
   - istnienie modelu i datasetu,
   - poprawność manifestu modelu,
   - `canStartTraining`,
   - zgodność profilu wejścia,
   - brak aktywnego runu.
9. `BE` generuje `runName` i `producedModelName`.
10. `BE` zapisuje rekord `trainings/metadata/{runName}.json`.
11. `BE` rozwiązuje wszystkie potrzebne ścieżki absolutne na podstawie `appsettings`.
12. `BE` wywołuje `POST /ml/trainings`.
13. `ML` przyjmuje run asynchronicznie i odsyła `202 Accepted`.
14. `BE` od razu zwraca `FE` odpowiedź startową z:
   - `runName`
   - `producedModelName`
   - `status`
   - `progressChannelUrl`
15. `FE` przechodzi do monitoringu runu i otwiera `WebSocket /ws/trainings/{runName}` z tokenem przekazanym przez `accessTokenFactory`.
16. `BE` po połączeniu wysyła `snapshot` aktualnego stanu runu.
17. `ML` wykonuje trening i wysyła kolejne eventy do `BE` przez `POST /internal/ml/trainings/{runName}/events`.
18. `BE` aktualizuje własny rekord runu i dopiero wtedy publikuje ten stan do `FE`.
19. `ML` zapisuje:
   - checkpointy i logi do `trainings/runs/{runName}`,
   - raporty do `trainings/reports/{runName}`,
   - finalne artefakty modelu do `models/registry/{producedModelName}/artifacts`.
20. Po zdarzeniu końcowym `BE` finalizuje `models/registry/{producedModelName}/model.json`.
21. Run staje się widoczny w późniejszych use case'ach:
   - `UC-07` postęp,
   - `UC-08` lista treningów i modeli,
   - `UC-09` szczegóły i metryki,
   - `UC-10` aktywacja modelu.

## Jak `FE` dostaje postęp bez rozmowy z `ML`
- `ML` nie rozmawia z `FE`.
- Zamiast tego:
  1. `ML` wysyła event do `BE`.
  2. `BE` zapisuje nowy stan runu.
  3. `BE` wypycha event do `FE`.
- Dzięki temu:
  - `BE` pozostaje właścicielem statusu,
  - `FE` ma realtime update,
  - odświeżenie strony nie gubi stanu biznesowego.

## Utrata połączenia `WebSocket`
- Zerwanie `WebSocket` nie zatrzymuje runu.
- Run trwa dalej po stronie `ML`.
- `ML` dalej raportuje do `BE`.
- `BE` dalej aktualizuje rekord runu.
- Po reconnect `FE` powinno:
  - ponownie połączyć kanał,
  - odebrać `snapshot`,
  - opcjonalnie odtworzyć stan przez `GET /api/trainings/{runName}` z późniejszego use case'u.

## Anulowanie runu
- Użytkownik może anulować aktywny run.
- `FE` wysyła `POST /api/trainings/{runName}/cancel`.
- `BE` przechodzi do stanu `cancelling` i wywołuje `POST /ml/trainings/{runName}/cancel`.
- `ML` ustawia własną flagę anulowania i sprawdza ją między bezpiecznymi etapami pracy.
- Po bezpiecznym przerwaniu `ML` wysyła event `cancelled` do `BE`.
- `BE` zapisuje stan końcowy i publikuje go do `FE`.

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

## Pliki i odpowiedzialność
### Co zapisuje `BE`
- `trainings/metadata/{runName}.json`
- finalne `models/registry/{producedModelName}/model.json`

### Co zapisuje `ML`
- `trainings/runs/{runName}`
- `trainings/reports/{runName}`
- `models/registry/{producedModelName}/artifacts`

## Uszkodzony raport a używalny model
- Błąd raportu nie musi oznaczać, że run jest całkowicie bezużyteczny.
- Jeśli finalne artefakty modelu są kompletne, ale raport jest uszkodzony:
  - run może zakończyć się sukcesem,
  - `reportStatus` może mieć wartość `corrupted` albo `missing`,
  - UI powinno pokazać ostrzeżenie o raporcie,
  - model może nadal być dostępny do aktywacji i inferencji.

## Najważniejsze zasady architektoniczne
- `FE` wybiera tylko nazwy logiczne, nigdy ścieżki systemowe.
- `BE` jest właścicielem workflow, statusów i rekordów systemowych.
- `ML` wykonuje pracę techniczną i raportuje do `BE`.
- `runName` identyfikuje proces treningowy, nie model.
- Model bootstrap może nie mieć `runName`.
- System nie buduje kolejki runów.
- Utrata `WebSocket` nie zatrzymuje treningu.
