namespace Sudoku.Application.Trainings;

public sealed record TrainingRunEventResultDto(
    string? ProducedModelName,
    string? PrimaryArtifactRelativePath,
    string? ReportStatus,
    string? ReportRelativePath,
    TrainingMetricsSummaryDto? MetricsSummary);
