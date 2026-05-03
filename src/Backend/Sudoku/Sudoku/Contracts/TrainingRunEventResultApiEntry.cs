namespace Sudoku.Contracts;

public sealed record TrainingRunEventResultApiEntry(
    string? ProducedModelName,
    string? PrimaryArtifactRelativePath,
    string? ReportStatus,
    string? ReportRelativePath,
    bool? CanUseProducedModelForInference,
    TrainingMetricsSummaryApiEntry? MetricsSummary);
