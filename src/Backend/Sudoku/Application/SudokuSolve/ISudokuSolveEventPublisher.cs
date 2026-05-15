namespace Sudoku.Application.SudokuSolve;

public interface ISudokuSolveEventPublisher
{
    Task PublishAsync(
        SolveSessionProgressSnapshotDto snapshot,
        CancellationToken cancellationToken = default);
}
