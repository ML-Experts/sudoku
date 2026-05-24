namespace Sudoku.Application.Trainings;

public sealed record ActiveTrainingRunDto(
    string RunName,
    string Status,
    DateTimeOffset CreatedAtUtc,
    string BaseModelName,
    string ProducedModelName,
    string ProcessedDatasetName,
    string TrainingMode,
    string TrainingProfileName,
    string AugmentationProfileName,
    string BenchmarkName,
    int Seed,
    TrainingRunEffectiveParametersDto? EffectiveParameters,
    string ProgressChannelUrl);
