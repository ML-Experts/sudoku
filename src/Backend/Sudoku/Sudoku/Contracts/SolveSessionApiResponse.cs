namespace Sudoku.Contracts;

public sealed record SolveSessionApiResponse(
    string SolveSessionId,
    string Status,
    string ProgressChannelUrl);
