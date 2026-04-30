namespace Sudoku.Contracts;

public sealed record TrainingMetricsSummaryApiEntry(
    decimal? Accuracy,
    decimal? MacroF1);
