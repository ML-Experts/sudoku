namespace Sudoku.Application.SudokuSolve;

public sealed record StartSudokuSolveCommandResultDto(
    string SolveSessionId,
    string Status,
    string ProgressChannelUrl);
