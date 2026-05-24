namespace Sudoku.Contracts;

public sealed record CreateTrainingRunApiEntry(
    string? BaseModelName,
    string? ProcessedDatasetName,
    CreateTrainingRunParametersApiEntry? TrainingParameters);

public sealed record CreateTrainingRunParametersApiEntry(
    int? Epochs,
    double? LearningRate,
    int? BatchSize,
    int? EarlyStoppingPatience,
    int? LrSchedulerPatience,
    double? LrSchedulerFactor,
    string? FineTuningPolicy);
