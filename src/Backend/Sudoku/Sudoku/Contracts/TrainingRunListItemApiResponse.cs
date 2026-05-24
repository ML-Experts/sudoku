namespace Sudoku.Contracts;

public sealed record TrainingRunListItemApiResponse(
    string RunName,
    string Status,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset? UpdatedAtUtc,
    DateTimeOffset? StartedAtUtc,
    DateTimeOffset? FinishedAtUtc,
    string BaseModelName,
    string ProducedModelName,
    string ProcessedDatasetName,
    string TrainingMode,
    string TrainingProfileName,
    string AugmentationProfileName,
    string BenchmarkName,
    TrainingRunEffectiveParametersApiResponse? EffectiveParameters,
    string? ReportStatus,
    TrainingRunProgressApiResponse? Progress,
    TrainingMetricsSummaryApiResponse? MetricsSummary,
    IReadOnlyList<string> Warnings);
