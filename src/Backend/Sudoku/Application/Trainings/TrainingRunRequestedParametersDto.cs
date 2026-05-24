namespace Sudoku.Application.Trainings;

public sealed record TrainingRunRequestedParametersDto(
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
