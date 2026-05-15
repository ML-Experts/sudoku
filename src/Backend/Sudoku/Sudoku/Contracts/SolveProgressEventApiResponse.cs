namespace Sudoku.Contracts;

public sealed record SolveProgressEventApiResponse(
    string EventType,
    string SolveSessionId,
    string Status,
    long Sequence,
    int?[][] CurrentGrid,
    string? ErrorType,
    string? Message);
