namespace Sudoku.Models.Sudoku;

public static class SudokuSolveEventType
{
    public const string Snapshot = "snapshot";
    public const string Progress = "progress";
    public const string Completed = "completed";
    public const string Failed = "failed";
    public const string Cancelled = "cancelled";
}
