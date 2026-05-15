using Sudoku.Models.Sudoku;

namespace Sudoku.Application.SudokuSolve;

public interface ISudokuBacktrackingSolver
{
    Task<SudokuBacktrackingSolveResultDto> SolveAsync(
        SudokuGrid grid,
        Func<SudokuSolverStepDto, CancellationToken, Task> onStepAsync,
        CancellationToken cancellationToken = default);
}
