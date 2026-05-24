namespace Sudoku.Application.Trainings;

public sealed record TrainingRunEventResultDto(
    string? ProducedModelName,
    string? PrimaryArtifactRelativePath,
    string? ReportStatus,
    string? ReportRelativePath,
    string? SummaryRelativePath,
    string? MetricsRelativePath,
    string? ConfusionMatrixRelativePath,
    bool? CanUseProducedModelForInference,
    TrainingMetricsSummaryDto? MetricsSummary);
