namespace Sudoku.Contracts;

public sealed record TrainingRunEventApiEntry(
    long Sequence,
    string? RunName,
    string? EventType,
    string? Status,
    string? Stage,
    DateTimeOffset OccurredAtUtc,
    string? Message,
    TrainingRunProgressApiEntry? Progress,
    TrainingRunEventResultApiEntry? Result,
    TrainingRunFailureApiEntry? Failure,
    IReadOnlyList<string>? Warnings);

public sealed record TrainingRunFailureApiEntry(
    string? ErrorType,
    string? Message,
    bool? CanUseProducedModelForInference);
