namespace Sudoku.Application.Trainings;

public sealed record TrainingMetricsSummaryDto(
    decimal? Accuracy,
    decimal? MacroF1);
