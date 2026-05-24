# UC-10 — Wybierz aktywny model

## Cel
- Pozwolić użytkownikowi wybrać aktywny model z rejestru modeli na podstawie skróconych metryk i capability.
- Utrzymać `Backend` jako `source of truth` dla aktywnego modelu przez zapis lekkiego wskaźnika `models/active/inference.json`.
- Zapisać wybór bez kopiowania katalogu modelu i bez tworzenia drugiego źródła prawdy po stronie `FE` albo `ML`.

## Diagram przepływu
```mermaid
flowchart TD
    A[FE: otwiera wybór aktywnego modelu] -->|FE -> BE<br/>GET /api/models/registry| B[BE: czyta rejestr modeli<br/>read models/registry/*/model.json]
    A -->|FE -> BE<br/>GET /api/models/active| C[BE: czyta wskaźnik aktywny<br/>read models/active/inference.json]

    B --> D[BE: zwraca modele z capability i metrykami skrótowymi]
    C --> E{Aktywny model ustawiony?}

    E -->|tak<br/>200 OK| F[FE: zaznacza aktualny model]
    E -->|nie<br/>204 No Content| G[FE: pokazuje brak aktywnego modelu]

    D --> H[FE: filtruje / wyróżnia modele canUseForInference]
    F --> H
    G --> H

    H --> I[FE: użytkownik wybiera model]
    I -->|FE -> BE<br/>PUT /api/models/active| J[BE: waliduje modelName<br/>read models/registry/{modelName}/model.json]

    J --> K{Model może być aktywny?}
    K -->|nie<br/>400 / 404 / 409 / 422| L[FE: pokazuje błąd wyboru]

    K -->|tak| M[BE: zapisuje wskaźnik atomowo<br/>write models/active/inference.json]
    M -->|BE -> FE<br/>200 ActiveModelApiResponse| N[FE: pokazuje nowy aktywny model]

    %% FE -> BE
    linkStyle 0,1,9 stroke:#2563eb,stroke-width:2px

    %% BE -> FE
    linkStyle 4,5,12 stroke:#16a34a,stroke-width:2px

    %% Internal
    linkStyle 2,3,6,7,8,10,11,13 stroke:#7c3aed,stroke-width:1.5px
```

## Role warstw
### `FE`
- Pobiera rejestr modeli przez `GET /api/models/registry`.
- Pobiera aktualny aktywny model przez `GET /api/models/active`.
- Pozwala wybrać tylko model widoczny jako dopuszczony do aktywacji (`canUseForInference = true`), ale nie traktuje filtrowania UI jako walidacji bezpieczeństwa.
- Wysyła wybór przez `PUT /api/models/active`.

### `BE`
- Jest właścicielem publicznych endpointów aktywnego modelu.
- Waliduje, że wskazany model istnieje w `models/registry/{modelName}/model.json`, ma `canUseForInference = true`, kompletny manifest i dostępny główny artefakt.
- Aktualizuje wyłącznie wskaźnik `models/active/inference.json`; nie kopiuje katalogu `models/registry/{modelName}`.
- Mapuje aktywny model na publiczny kontrakt dla `FE`.

### `ML`
- Nie udostępnia osobnego publicznego wyboru modelu.
- Nie zapisuje aktywnego modelu samodzielnie po starcie aplikacji, poza bootstrapowym utworzeniem wskaźnika, jeśli nie istnieje.
- Korzysta z tego samego kontraktu plikowego, ale nie staje się właścicielem wyboru użytkownika.

## Kontrakty `FE -> BE`
### `GET /api/models/registry`
- Endpoint chroniony tokenem administracyjnym z `UC-13`.
- `200 OK` -> `RegistryModelsListApiResponse`.
- Dla `UC-10` kluczowe pola elementu listy to:
  - `name`,
  - `displayName`,
  - `sourceType`,
  - `sourceRunName`,
  - `parentModelName`,
  - `inputProfile`,
  - `createdAtUtc`,
  - `canUseForInference`,
  - `warnings`,
  - opcjonalnie `metricsSummary`, jeśli zostanie dopisane po `UC-09`.

Ten endpoint korzysta z danych zapisanych w `models/registry/{modelName}/model.json`; `FE` nie czyta tych plików bezpośrednio.

### `GET /api/models/active`
- Endpoint chroniony tokenem administracyjnym z `UC-13`.
- `200 OK` -> `ActiveModelApiResponse`, jeśli aktywny model jest ustawiony i nadal poprawny.
- `204 No Content`, jeśli wskaźnik nie istnieje.
- `409 Conflict` -> `ErrorApiResponse`, jeśli wskaźnik istnieje, ale wskazuje model, którego nie można aktywować.

```json
{
  "modelName": "train-20260503-112233",
  "displayName": "train-20260503-112233",
  "sourceType": "training",
  "sourceRunName": "train-20260503-112233",
  "parentModelName": "cnn-bootstrap",
  "inputProfile": "default-28x28-v1",
  "canUseForInference": true,
  "activatedAtUtc": "2026-05-03T11:05:00Z"
}
```

### `PUT /api/models/active`
- Endpoint chroniony tokenem administracyjnym z `UC-13`.
- Request body: `SetActiveModelApiEntry`.
- `200 OK` -> `ActiveModelApiResponse`.

```json
{
  "modelName": "train-20260503-112233"
}
```

```json
{
  "modelName": "train-20260503-112233",
  "displayName": "train-20260503-112233",
  "sourceType": "training",
  "sourceRunName": "train-20260503-112233",
  "parentModelName": "cnn-bootstrap",
  "inputProfile": "default-28x28-v1",
  "canUseForInference": true,
  "activatedAtUtc": "2026-05-03T11:05:00Z"
}
```

Reguły odpowiedzi błędnych:
- `400 Bad Request` -> niepoprawny lub pusty `modelName`.
- `404 Not Found` -> brak wpisu `models/registry/{modelName}/model.json`.
- `409 Conflict` -> model istnieje, ale ma `canUseForInference = false`.
- `422 Unprocessable Entity` -> manifest albo ścieżka artefaktu są niekompletne lub niebezpieczne.
- Wszystkie błędy używają `ErrorApiResponse` z polami `errorType` i `message`.

## Pliki danych jako kontrakty systemu
### `models/active/inference.json`
To jest główny rekord stanu dla `UC-10`. Plik wskazuje, który wpis z rejestru modeli jest aktualnie wybrany jako aktywny. Zmiana aktywnego modelu oznacza zmianę tego pliku, a nie kopiowanie katalogu modelu.

```json
{
  "modelName": "train-20260503-112233",
  "registryRelativePath": "../registry/train-20260503-112233",
  "setBy": "backend",
  "updatedAtUtc": "2026-05-03T11:05:00Z"
}
```

Semantyka pól:
- `modelName` jest jedynym wymaganym identyfikatorem modelu i musi być nazwą katalogu bez separatorów ścieżek.
- `registryRelativePath` jest polem informacyjnym / diagnostycznym; komponenty systemu powinny rozwiązywać model względem skonfigurowanego katalogu rejestru.
- `setBy` opisuje źródło zapisu (`backend` albo `init_bootstrap`).
- `updatedAtUtc` pozwala odróżnić kolejne zmiany wyboru, ale brak tego pola w istniejącym pliku bootstrapowym nie powinien blokować odczytu, jeśli `modelName` jest poprawny.

### `models/registry/{modelName}/model.json`
Drugi kontrakt plikowy jest współdzielony z `UC-06`, `UC-08` i `UC-09`. `UC-10` nie zmienia jego celu, ale zaostrza sposób użycia: model może zostać aktywowany tylko wtedy, gdy manifest ma kompletne dane wymagane przez capability.

Minimalne pola wymagane dla aktywacji:

```json
{
  "name": "train-20260503-112233",
  "displayName": "train-20260503-112233",
  "sourceType": "training",
  "sourceRunName": "train-20260503-112233",
  "parentModelName": "cnn-bootstrap",
  "framework": "pytorch",
  "architecture": {
    "type": "cnn",
    "family": "sudoku-digit-classifier",
    "numClasses": 10,
    "inputChannels": 1,
    "inputHeight": 28,
    "inputWidth": 28,
    "inputProfile": "default-28x28-v1"
  },
  "artifacts": {
    "primaryArtifactRelativePath": "artifacts/model.pt",
    "format": "pytorch-state-dict"
  },
  "capabilities": {
    "canStartTraining": true,
    "canUseForInference": true
  }
}
```

### `trainings/reports/{runName}/{summaryRelativePath}`
Ten plik nie jest zapisywany przez `UC-10`, ale może zasilać skrócone metryki widoczne przy wyborze modelu, jeśli model pochodzi z treningu.

Minimalny zakres danych używany w wyborze aktywnego modelu:

```json
{
  "runName": "train-20260503-112233",
  "producedModelName": "train-20260503-112233",
  "benchmarkName": "sudoku-benchmark-v1",
  "metricsSummary": {
    "accuracy": 0.96,
    "macroF1": 0.95
  }
}
```

`UC-10` tylko prezentuje te dane w kontekście wyboru. Jeśli raportu brakuje, model nadal może być możliwy do wyboru, o ile `models/registry/{modelName}/model.json` deklaruje poprawne capability.

Nazwa konkretnego pliku raportu nie jest ustalana przez `UC-10`; pochodzi z referencji `summaryRelativePath` zapisanej dla runu w `UC-06`.

## Pliki danych istotne dla `UC-10`
- `models/active/inference.json` — jedyny rekord aktywnego modelu.
- `models/registry/{modelName}/model.json` — manifest modelu i źródło capability `canUseForInference`.
- `models/registry/{modelName}/{primaryArtifactRelativePath}` — główny artefakt modelu wskazany przez manifest.
- `trainings/reports/{runName}/{summaryRelativePath}` — opcjonalne źródło metryk skrótowych pokazywanych przy wyborze modelu.

## Przesunięcia plików danych
- Nie przenosić `models/active/inference.json` pod `models/registry`; aktywny wskaźnik pozostaje osobnym lekkim rekordem stanu systemu.
- Nie kopiować katalogu artefaktów z `models/registry/{modelName}` do `models/active`; przełączenie aktywnego modelu zmienia wyłącznie wskaźnik.
- Nie tworzyć osobnej bazy aktywnego modelu po stronie `FE` ani `ML`; wybór użytkownika jest utrwalony tylko w `models/active/inference.json`.

## Kryteria akceptacji
- Użytkownik widzi listę modeli i może wybrać jako aktywny tylko model z poprawnym `canUseForInference = true`.
- `PUT /api/models/active` aktualizuje `models/active/inference.json` atomowo i nie kopiuje katalogu modelu.
- Backend odrzuca model brakujący, uszkodzony albo z `canUseForInference = false`.
- Wybór aktywnego modelu jest zapisany tylko we wskaźniku `models/active/inference.json`.
- `ML` nie utrzymuje osobnego źródła prawdy aktywnego modelu; korzysta ze wskaźnika i manifestu rejestru.
- Publiczne payloady używają `camelCase`, a błędy API używają `ErrorApiResponse`.
