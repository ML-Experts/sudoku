namespace Sudoku.Application.SudokuSolve;

public sealed record SolveSessionProgressSnapshotDto(
    string SolveSessionId,
    string Status,
    string ProgressChannelUrl,
    int?[][] InputGrid,
    int?[][] CurrentGrid,
    long? Sequence,
    string? EventType,
    string? FailureErrorType,
    string? FailureMessage,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc,
    DateTimeOffset? StartedAtUtc,
    DateTimeOffset? FinishedAtUtc);
