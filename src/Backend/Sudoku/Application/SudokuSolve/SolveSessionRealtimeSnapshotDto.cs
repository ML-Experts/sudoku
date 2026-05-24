namespace Sudoku.Application.SudokuSolve;

public sealed record SolveSessionRealtimeSnapshotDto(
    string SolveSessionId,
    string Status,
    long Sequence,
    string EventType,
    int?[][] CurrentGrid,
    string? FailureErrorType,
    string? FailureMessage,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc,
    DateTimeOffset? StartedAtUtc,
    DateTimeOffset? FinishedAtUtc);
