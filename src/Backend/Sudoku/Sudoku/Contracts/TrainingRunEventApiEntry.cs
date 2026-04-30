namespace Sudoku.Contracts;

public sealed record TrainingRunEventApiEntry(
    long Sequence,
    string? EventType,
    string? Status,
    DateTimeOffset OccurredAtUtc,
    string? Message,
    TrainingRunProgressApiEntry? Progress,
    TrainingRunEventResultApiEntry? Result,
    IReadOnlyList<string>? Warnings);
