namespace Sudoku.Application.SudokuSolve;

public sealed record SudokuBacktrackingSolveResultDto(string Outcome)
{
    public const string Completed = "completed";
    public const string Unsolvable = "unsolvable";
    public const string Cancelled = "cancelled";

    public static SudokuBacktrackingSolveResultDto CompletedResult() => new(Completed);

    public static SudokuBacktrackingSolveResultDto UnsolvableResult() => new(Unsolvable);

    public static SudokuBacktrackingSolveResultDto CancelledResult() => new(Cancelled);
}
