namespace Sudoku.Application.Trainings;

public sealed record TrainingReportArtifactsDto(
    string? SummaryRelativePath,
    string? MetricsRelativePath,
    string? ConfusionMatrixRelativePath);
