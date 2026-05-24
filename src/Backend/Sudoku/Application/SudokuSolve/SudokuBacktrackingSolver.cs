using Sudoku.Models.Sudoku;

namespace Sudoku.Application.SudokuSolve;

public sealed class SudokuBacktrackingSolver : ISudokuBacktrackingSolver
{
    public async Task<SudokuBacktrackingSolveResultDto> SolveAsync(
        SudokuGrid grid,
        Func<SudokuSolverStepDto, CancellationToken, Task> onStepAsync,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(grid);
        ArgumentNullException.ThrowIfNull(onStepAsync);

        return await TrySolveRecursiveAsync(grid, onStepAsync, cancellationToken);
    }

    private static async Task<SudokuBacktrackingSolveResultDto> TrySolveRecursiveAsync(
        SudokuGrid grid,
        Func<SudokuSolverStepDto, CancellationToken, Task> onStepAsync,
        CancellationToken cancellationToken)
    {
        if (cancellationToken.IsCancellationRequested)
        {
            return SudokuBacktrackingSolveResultDto.CancelledResult();
        }

        var selection = SelectMostConstrainedEmptyCell(grid);
        if (selection is null)
        {
            return SudokuBacktrackingSolveResultDto.CompletedResult();
        }

        if (selection.Candidates.Count == 0)
        {
            return SudokuBacktrackingSolveResultDto.UnsolvableResult();
        }

        foreach (var digit in selection.Candidates)
        {
            if (cancellationToken.IsCancellationRequested)
            {
                return SudokuBacktrackingSolveResultDto.CancelledResult();
            }

            grid.SetSolverDigit(selection.Position, digit);
            await onStepAsync(
                new SudokuSolverStepDto(
                    EventType: SudokuSolveEventType.Progress,
                    CurrentGrid: grid.ToJaggedArray(),
                    Position: selection.Position,
                    Digit: digit),
                cancellationToken);

            var result = await TrySolveRecursiveAsync(grid, onStepAsync, cancellationToken);
            if (!string.Equals(
                    result.Outcome,
                    SudokuBacktrackingSolveResultDto.Unsolvable,
                    StringComparison.Ordinal))
            {
                return result;
            }

            grid.ClearSolverDigit(selection.Position);
            await onStepAsync(
                new SudokuSolverStepDto(
                    EventType: SudokuSolveEventType.Progress,
                    CurrentGrid: grid.ToJaggedArray(),
                    Position: selection.Position,
                    Digit: null),
                cancellationToken);
        }

        return SudokuBacktrackingSolveResultDto.UnsolvableResult();
    }

    private static CellSelection? SelectMostConstrainedEmptyCell(SudokuGrid grid)
    {
        CellSelection? bestSelection = null;

        foreach (var position in grid.EnumerateEmptyCells())
        {
            var candidates = SudokuGridRules.GetAllowedDigits(grid, position);
            var selection = new CellSelection(position, candidates);

            if (selection.Candidates.Count == 0)
            {
                return selection;
            }

            if (bestSelection is null || selection.Candidates.Count < bestSelection.Candidates.Count)
            {
                bestSelection = selection;
            }
        }

        return bestSelection;
    }

    private sealed record CellSelection(
        SudokuCellPosition Position,
        IReadOnlyList<int> Candidates);
}
