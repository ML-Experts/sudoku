namespace Sudoku.Application.SudokuSolve;

public sealed record GetActiveSolveSessionQueryResultDto(
    bool HasActiveSession,
    ActiveSolveSessionDto? Session);
