namespace Sudoku.Application.Trainings;

public sealed record TrainingRunRequestedParametersDto(
    int? Epochs,
    double? LearningRate,
    int? BatchSize,
    int? EarlyStoppingPatience,
    int? LrSchedulerPatience,
    double? LrSchedulerFactor,
    string? FineTuningPolicy);
