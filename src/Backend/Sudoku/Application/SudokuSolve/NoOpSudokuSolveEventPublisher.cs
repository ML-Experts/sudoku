namespace Sudoku.Application.SudokuSolve;

public sealed class NoOpSudokuSolveEventPublisher : ISudokuSolveEventPublisher
{
    public Task PublishAsync(
        SolveSessionProgressSnapshotDto snapshot,
        CancellationToken cancellationToken = default)
    {
        return Task.CompletedTask;
    }
}
