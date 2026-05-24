namespace Sudoku.Application.SudokuSolve;

public sealed record SolveSessionMetadataDto(
    string SolveSessionId,
    string Status,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc,
    string ProgressChannelUrl,
    int?[][] InputGrid,
    int?[][] CurrentGrid,
    long? LastAcceptedSequence = null,
    string? LastEventType = null,
    string? FailureErrorType = null,
    string? FailureMessage = null,
    DateTimeOffset? StartedAtUtc = null,
    DateTimeOffset? FinishedAtUtc = null,
    SudokuSolveEffectiveParametersDto? EffectiveParameters = null);
