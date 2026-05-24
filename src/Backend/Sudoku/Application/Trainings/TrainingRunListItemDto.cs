namespace Sudoku.Application.Trainings;

public sealed record TrainingRunListItemDto(
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
    TrainingRunEffectiveParametersDto? EffectiveParameters,
    string? ReportStatus,
    TrainingRunProgressDto? Progress,
    TrainingMetricsSummaryDto? MetricsSummary,
    IReadOnlyList<string> Warnings);
