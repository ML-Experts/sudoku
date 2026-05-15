namespace Sudoku.Application.SudokuSolve;

public sealed record ActiveSolveSessionDto(
    string SolveSessionId,
    string Status,
    string ProgressChannelUrl);
