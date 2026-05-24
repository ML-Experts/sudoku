namespace Sudoku.Application.SudokuSolve;

public interface ISolveSessionLockProvider
{
    ValueTask<IAsyncDisposable> AcquireAsync(
        string solveSessionId,
        CancellationToken cancellationToken = default);
}
