namespace Sudoku.Contracts;

public sealed record TrainingRunSocketEventApiResponse(
    string EventType,
    long Sequence,
    string RunName,
    string Status,
    string Stage,
    DateTimeOffset OccurredAtUtc,
    string? Message,
    TrainingRunProgressApiResponse? Progress,
    IReadOnlyList<string> Warnings,
    TrainingRunResultApiResponse? Result,
    TrainingRunFailureApiResponse? Failure);

public sealed record TrainingRunResultApiResponse(
    string ProducedModelName,
    string ReportStatus,
    bool CanUseProducedModelForInference,
    string PrimaryArtifactRelativePath,
    string? SummaryRelativePath,
    string? MetricsRelativePath,
    string? ConfusionMatrixRelativePath,
    TrainingMetricsSummaryApiResponse? MetricsSummary);

public sealed record TrainingRunFailureApiResponse(
    string ErrorType,
    string Message,
    bool CanUseProducedModelForInference);
