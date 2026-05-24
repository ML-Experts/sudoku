namespace Sudoku.Contracts;

public sealed record TrainingRunApiResponse(
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
    TrainingRunEffectiveParametersApiResponse? EffectiveParameters,
    string ProgressChannelUrl);
