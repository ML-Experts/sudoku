# ML Training Flow

## Cel
Ten dokument pokazuje, jak w projekcie przebiega trening modelu od żądania HTTP aż do pojawienia się nowego wpisu w rejestrze modeli oraz osobnej aktywacji modelu do inferencji.

## Najważniejsza zasada architektoniczna
- Backend jest `source of truth` dla workflow treningów, statusów runów, rejestru modeli i aktywnego modelu.
- Serwis `MachineLearning` wykonuje trening, zapisuje artefakty techniczne i wysyła zdarzenia do backendu.
- Samo zakończenie treningu nie aktywuje automatycznie modelu do inferencji.

## Mermaid
```mermaid
flowchart TD
    A[Uzytkownik / FE\nPOST /api/trainings] --> B[Backend\nCreateTrainingRunCommandHandler]
    B --> C[Backend sprawdza:\n- aktywny run\n- model bazowy z registry\n- processed dataset\n- zgodnosc input profile]
    C --> D[Backend rezerwuje run\nstatus=starting]
    D --> E[Backend buduje request do ML:\n- manifestPath\n- primaryArtifactPath\n- outputModel.directoryPath\n- outputPaths.report/run/tmp]
    E --> F[ML\nPOST /ml/trainings]

    F --> G[trainings_controller.py]
    G --> H[StartTrainingRunCommandHandler]
    H --> I[ML waliduje:\n- istnienie plikow\n- dozwolone output paths\n- manifest\n- training_mode=fineTuning]
    I --> J[ML odczytuje manifest modelu bazowego]
    J --> K[ML rezerwuje cancellation token]
    K --> L[BackgroundTasks.add_task\ntraining_runner.start(...)]
    L --> M[HTTP 202 Accepted]

    M --> N[PytorchTrainingRunner.start]
    N --> O[Publikacja eventu statusChanged\nstatus=running]
    O --> P[Budowa modelu z manifestu]
    P --> Q[Zaladowanie wag modelu bazowego]
    Q --> R[Wczytanie datasetu .npz]
    R --> S[Dobor profilu, optimizera,\naugmentacji, scheduler]
    S --> T[Petla epok:\ntrain + val + checkpointy + progress events]
    T --> U[Ewaluacja najlepszego checkpointu]
    U --> V[Zapis wag wynikowego modelu\nModelArtifactWriter.write]
    V --> W[Zapis raportow\nsummary.json / metrics.json / confusion_matrix.json]
    W --> X[Publikacja eventu completed\nz artifactRelativePath i report paths]

    X --> Y[Backend\nRecordTrainingRunEventCommandHandler]
    Y --> Z[Backend aktualizuje status runu]
    Z --> AA[FinalizeTrainedModelAsync]
    AA --> AB[Backend zapisuje registry/{modelName}/model.json]
    AB --> AC[Nowy model istnieje w registry]

    AC --> AD{Czy model ma byc aktywny\nw inferencji?}
    AD -->|nie| AE[Koniec - model tylko w registry]
    AD -->|tak, osobna akcja| AF[PUT /api/models/active]
    AF --> AG[SetActiveModelCommandHandler]
    AG --> AH[Backend zapisuje models/active/inference.json]
    AH --> AI[ActiveModelResolver rozwiazuje:\nmodel.json + artifact path]
    AI --> AJ[Backend przekazuje aktywny model do ML\nprzy requestach inferencyjnych]
```

## Skrót odpowiedzialności
### Backend
- wybiera model bazowy i dataset,
- pilnuje, że jest tylko jeden aktywny run,
- generuje nazwę runu i katalog modelu wynikowego,
- wysyła request do ML,
- po evencie `completed` zapisuje finalny `model.json` do rejestru,
- osobno ustawia aktywny model przez `models/active/inference.json`.

### MachineLearning
- przyjmuje request startu treningu,
- waliduje wejście i manifest,
- uruchamia trening w tle,
- buduje model i ładuje bazowe wagi,
- trenuje, zapisuje checkpointy, zapisuje finalne wagi i raporty,
- wysyła eventy `statusChanged`, `progress`, `completed` / `failed` / `cancelled`.

## Co jest parametrem treningu
Parametry są składane w backendzie i przekazywane do ML w requestcie startowym. Najważniejsze grupy:
- model bazowy: nazwa, `manifestPath`, `primaryArtifactPath`, `inputProfile`,
- dataset: ścieżka do pliku `.npz` i profil preprocessingu,
- resolved configuration: `trainingMode`, `trainingProfileName`, `augmentationProfileName`, `benchmarkName`, `seed`,
- output model: nazwa i katalog docelowy nowego modelu,
- output paths: katalog runu, raportów i katalog tymczasowy.

## Co oznacza "publikacja modelu" w tym projekcie
W praktyce są tu dwa osobne kroki:

1. `ML` konczy trening i zapisuje artefakt `.pt` oraz raporty.
2. `Backend` po evencie `completed` dopiero finalizuje wpis registry przez zapis `model.json`.

To jeszcze nie znaczy, ze model jest aktywny dla inferencji.

## Co oznacza "aktywacja modelu"
Aktywacja to osobny use-case backendu:
- backend wybiera model z registry,
- sprawdza, czy model nadaje sie do inferencji,
- zapisuje pointer `models/active/inference.json`,
- od tej chwili ten model jest rozwiazywany jako aktywny przez `ActiveModelResolver`.
