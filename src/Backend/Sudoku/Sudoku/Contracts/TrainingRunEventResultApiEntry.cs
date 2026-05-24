namespace Sudoku.Contracts;

public sealed record TrainingRunEventResultApiEntry(
    string? ProducedModelName,
    string? PrimaryArtifactRelativePath,
    string? ReportStatus,
    string? ReportRelativePath,
    string? SummaryRelativePath,
    string? MetricsRelativePath,
    string? ConfusionMatrixRelativePath,
    bool? CanUseProducedModelForInference,
    TrainingMetricsSummaryApiEntry? MetricsSummary);
