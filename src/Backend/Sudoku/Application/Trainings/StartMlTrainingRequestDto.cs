namespace Sudoku.Application.Trainings;

public sealed record StartMlTrainingRequestDto(
    string RunName,
    StartMlTrainingBaseModelDto BaseModel,
    StartMlTrainingDatasetDto Dataset,
    StartMlTrainingSettingsDto Training,
    StartMlTrainingOutputDto Output,
    StartMlTrainingCallbacksDto Callbacks);

public sealed record StartMlTrainingBaseModelDto(
    string Name,
    string ManifestPath,
    string PrimaryArtifactPath,
    string InputProfile);

public sealed record StartMlTrainingDatasetDto(
    string Name,
    string ArtifactPath,
    string PreprocessingProfile);

public sealed record StartMlTrainingSettingsDto(
    string Mode,
    string TrainingProfileName,
    string AugmentationProfileName,
    string BenchmarkName,
    int Seed);

public sealed record StartMlTrainingOutputDto(
    string RunDirectoryPath,
    string ReportsDirectoryPath,
    string WorkingDirectoryPath,
    string ProducedModelName,
    string ProducedModelArtifactsDirectoryPath);

public sealed record StartMlTrainingCallbacksDto(
    string EventsPath);
