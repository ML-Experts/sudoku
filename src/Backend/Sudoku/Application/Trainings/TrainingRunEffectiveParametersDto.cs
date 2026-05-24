namespace Sudoku.Application.Trainings;

public sealed record TrainingRunEffectiveParametersDto(
    int Epochs,
    double LearningRate,
    int BatchSize,
    int EarlyStoppingPatience,
    int LrSchedulerPatience,
    double LrSchedulerFactor,
    string FineTuningPolicy,
    bool UseBestCheckpoint);
