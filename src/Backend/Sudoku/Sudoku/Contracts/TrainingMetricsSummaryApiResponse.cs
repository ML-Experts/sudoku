namespace Sudoku.Contracts;

public sealed record TrainingMetricsSummaryApiResponse(
    decimal? Accuracy,
    decimal? MacroF1);
