namespace Sudoku.Application.SudokuSolve;

public interface ISolveSessionIdGenerator
{
    string Generate(
        DateTimeOffset createdAtUtc,
        int attempt);
}
