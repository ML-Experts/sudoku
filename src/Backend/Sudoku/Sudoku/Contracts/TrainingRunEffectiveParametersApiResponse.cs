namespace Sudoku.Contracts;

public sealed record TrainingRunEffectiveParametersApiResponse(
    int Epochs,
    double LearningRate,
    int BatchSize,
    int EarlyStoppingPatience,
    int LrSchedulerPatience,
    double LrSchedulerFactor,
    string FineTuningPolicy);
