namespace Sudoku.Application.SudokuSolve;

public interface ISudokuSolveExecutionScheduler
{
    Task ScheduleAsync(
        SolveSessionWorkItemDto workItem,
        CancellationToken cancellationToken = default);
}
