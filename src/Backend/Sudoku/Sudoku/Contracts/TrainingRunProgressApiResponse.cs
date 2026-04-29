namespace Sudoku.Contracts;

public sealed record TrainingRunProgressApiResponse(
    decimal? Percent,
    int? Epoch,
    int? TotalEpochs,
    decimal? TrainLoss,
    decimal? ValidationLoss,
    decimal? TrainAccuracy,
    decimal? ValidationAccuracy);
