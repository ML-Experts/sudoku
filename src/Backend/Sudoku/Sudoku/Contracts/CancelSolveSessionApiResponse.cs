namespace Sudoku.Contracts;

public sealed record CancelSolveSessionApiResponse(
    string? Status,
    string RequestDisposition);
