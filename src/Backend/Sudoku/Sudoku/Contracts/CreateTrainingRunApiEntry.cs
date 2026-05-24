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
    double? EarlyStoppingMinDelta,
    int? WarmupEpochs,
    int? LrSchedulerPatience,
    double? LrSchedulerFactor,
    string? FineTuningPolicy,
    bool? UseBestCheckpoint);
