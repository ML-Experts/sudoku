namespace Sudoku.Contracts;

public sealed record TrainingRunEffectiveParametersApiResponse(
    int Epochs,
    double LearningRate,
    int BatchSize,
    int EarlyStoppingPatience,
    double EarlyStoppingMinDelta,
    int WarmupEpochs,
    int LrSchedulerPatience,
    double LrSchedulerFactor,
    string FineTuningPolicy,
    bool UseBestCheckpoint);
