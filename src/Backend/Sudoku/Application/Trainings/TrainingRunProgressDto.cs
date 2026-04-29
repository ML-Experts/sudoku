namespace Sudoku.Application.Trainings;

public sealed record TrainingRunProgressDto(
    decimal? Percent,
    int? Epoch,
    int? TotalEpochs,
    decimal? TrainLoss,
    decimal? ValidationLoss,
    decimal? TrainAccuracy,
    decimal? ValidationAccuracy);
