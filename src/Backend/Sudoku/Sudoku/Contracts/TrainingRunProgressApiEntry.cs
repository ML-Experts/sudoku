namespace Sudoku.Contracts;

public sealed record TrainingRunProgressApiEntry(
    decimal? Percent,
    int? EpochCurrent,
    int? EpochTotal,
    decimal? TrainLoss,
    decimal? ValidationLoss,
    decimal? TrainAccuracy,
    decimal? ValidationAccuracy,
    int? EtaSeconds);
