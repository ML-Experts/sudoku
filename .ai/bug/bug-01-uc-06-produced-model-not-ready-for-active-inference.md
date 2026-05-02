# BUG — UC-06 tworzy model niegotowy do przełączenia jako aktywny

## Status
- Typ: błąd domknięcia `UC-06`
- Obszar: `Backend` + `MachineLearning`
- Powiązane UC: `UC-06`, `UC-10`, `UC-05`
- Priorytet: wysoki, bo blokuje użycie wytrenowanego modelu w inferencji

## Problem
Po wykonaniu `UC-06` system potrafi uruchomić trening, zapisać artefakt modelu i utworzyć wpis w `models/registry/{producedModelName}`. Model wynikowy nie jest jednak w pełni gotowy do przełączenia jako aktywny model inferencyjny przez `models/active/inference.json`.

Sama obecność wpisu w rejestrze i artefaktu modelu nie wystarcza. Runtime inferencji po stronie `ML` potrzebuje pełnego manifestu technicznego `model.json`, aby wiedzieć:
- jaką architekturę zbudować,
- jakiego frameworka użyć,
- jaki format ma artefakt,
- jaki profil wejściowy zastosować,
- gdzie znajduje się główny artefakt modelu.

## Objaw
Model wytrenowany w `UC-06` może pojawić się w `GET /api/models/registry`, ale po wskazaniu go w `models/active/inference.json` nie nadaje się do użycia przez endpoint inferencji.

Eksperyment `EXP-04` pokazał, że inferencja oczekuje między innymi pól:

```json
{
  "framework": "pytorch",
  "architecture": {
    "type": "custom-cnn-v1",
    "family": "cnn",
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
    "canUseForInference": true
  }
}
```

Obecny manifest wynikowy po `UC-06` był wystarczający do listowania modelu w rejestrze, ale nie do runtime inferencji.

## Przyczyna
`UC-06` finalizuje wpis modelu wynikowego po zakończeniu treningu, ale finalizacja nie przenosi wszystkich technicznych metadanych wymaganych przez runtime inferencji.

Najważniejsze braki:
- `framework`,
- `architecture.type`,
- `architecture.family`,
- `architecture.numClasses`,
- `architecture.inputChannels`,
- `architecture.inputHeight`,
- `architecture.inputWidth`,
- `architecture.inputProfile`,
- `artifacts.primaryArtifactRelativePath`,
- `artifacts.format`,
- poprawne `capabilities.canUseForInference`.

## Decyzja architektoniczna
To jest błąd domknięcia `UC-06`, a nie zakres `UC-07`.

`UC-06` powinien produkować model gotowy do późniejszego przełączenia jako aktywny. Nie powinien jednak automatycznie przełączać aktywnego modelu.

Podział odpowiedzialności:
- `UC-06`: trenuje model, zapisuje artefakty i tworzy kompletny wpis `models/registry/{producedModelName}/model.json`.
- `UC-07`: pokazuje postęp i wynik treningu, może poinformować użytkownika, że model jest gotowy.
- `UC-10`: pozwala wybrać model aktywny i aktualizuje `models/active/inference.json`.
- `UC-05`: używa aktywnego modelu w inferencji.

## Proponowane rozwiązanie
Podczas finalizacji zakończonego sukcesem runu `Backend` powinien utworzyć pełny manifest modelu wynikowego.

Dla `fineTuning` w MVP:
1. `BE` odczytuje manifest modelu bazowego.
2. `BE` przepisuje techniczne pola architektury i wejścia z modelu bazowego, jeśli trening nie zmienia architektury.
3. `BE` uzupełnia metadane pochodzenia:
   - `sourceType = trained`,
   - `sourceRunName = runName`,
   - `parentModelName = baseModelName`,
   - `trainingMode = fineTuning`.
4. `BE` uzupełnia `artifacts.primaryArtifactRelativePath` i `artifacts.format` na podstawie wyniku zwróconego przez `ML`.
5. `BE` ustawia `capabilities.canUseForInference = true` tylko wtedy, gdy:
   - artefakt istnieje,
   - manifest zawiera wymagane pola,
   - `ML` zgłosił `canUseProducedModelForInference = true`.
6. Jeśli model nie spełnia warunków inferencji, wpis może pozostać w rejestrze, ale z `canUseForInference = false`.

## Kryteria akceptacji
- Model zakończony sukcesem w `UC-06` ma kompletny `model.json` wymagany przez runtime inferencji.
- Model wynikowy może zostać wskazany przez `models/active/inference.json` bez ręcznego poprawiania manifestu.
- `GET /api/models/registry` pokazuje poprawne `canUseForInference`.
- Jeśli raport treningu jest brakujący lub uszkodzony, ale artefakt inferencyjny i manifest są kompletne, model nadal może mieć `canUseForInference = true`.
- Jeśli artefakt albo manifest są niekompletne, model nie jest oznaczany jako gotowy do inferencji.
- `UC-06` nie przełącza automatycznie aktywnego modelu; robi to dopiero `UC-10`.

## Testy / weryfikacja
- Test finalizacji runu sprawdza, że `model.json` modelu wynikowego zawiera pełne pola techniczne.
- Test kontraktowy sprawdza, że model z `canUseForInference = true` może zostać załadowany przez mechanizm inferencji `ML`.
- Test negatywny sprawdza, że brak głównego artefaktu lub brak wymaganych pól manifestu skutkuje `canUseForInference = false`.
- Test regresyjny dla `fineTuning` sprawdza dziedziczenie architektury i profilu wejściowego z modelu bazowego.
