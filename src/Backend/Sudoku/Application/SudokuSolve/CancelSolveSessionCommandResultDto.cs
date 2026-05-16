namespace Sudoku.Application.SudokuSolve;

public sealed record CancelSolveSessionCommandResultDto(
    string? Status,
    string RequestDisposition);
