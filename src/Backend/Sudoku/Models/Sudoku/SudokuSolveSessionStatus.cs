namespace Sudoku.Models.Sudoku;

public static class SudokuSolveSessionStatus
{
    public const string Queued = "queued";
    public const string Running = "running";
    public const string Cancelling = "cancelling";
    public const string Completed = "completed";
    public const string Failed = "failed";
    public const string Cancelled = "cancelled";

    public static bool IsActive(string status)
    {
        return string.Equals(status, Queued, StringComparison.OrdinalIgnoreCase)
               || string.Equals(status, Running, StringComparison.OrdinalIgnoreCase)
               || string.Equals(status, Cancelling, StringComparison.OrdinalIgnoreCase);
    }

    public static bool IsTerminal(string status)
    {
        return string.Equals(status, Completed, StringComparison.OrdinalIgnoreCase)
               || string.Equals(status, Failed, StringComparison.OrdinalIgnoreCase)
               || string.Equals(status, Cancelled, StringComparison.OrdinalIgnoreCase);
    }

    public static bool CanRequestCancellation(string status)
    {
        return string.Equals(status, Queued, StringComparison.OrdinalIgnoreCase)
               || string.Equals(status, Running, StringComparison.OrdinalIgnoreCase);
    }
}
