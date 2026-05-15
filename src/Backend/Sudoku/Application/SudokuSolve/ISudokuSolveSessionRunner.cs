namespace Sudoku.Application.SudokuSolve;

public interface ISudokuSolveSessionRunner
{
    Task RunAsync(
        SolveSessionWorkItemDto workItem,
        CancellationToken cancellationToken = default);
}
