namespace Sudoku.Models.Trainings;

public static class TrainingRunStatus
{
    public const string Starting = "starting";
    public const string Queued = "queued";
    public const string Running = "running";
    public const string Cancelling = "cancelling";
    public const string Succeeded = "succeeded";
    public const string Failed = "failed";
    public const string Cancelled = "cancelled";

    public static bool IsTerminal(string status)
    {
        return string.Equals(status, Succeeded, StringComparison.OrdinalIgnoreCase)
               || string.Equals(status, Failed, StringComparison.OrdinalIgnoreCase)
               || string.Equals(status, Cancelled, StringComparison.OrdinalIgnoreCase);
    }

    public static bool IsActive(string status)
    {
        return string.Equals(status, Starting, StringComparison.OrdinalIgnoreCase)
               || string.Equals(status, Queued, StringComparison.OrdinalIgnoreCase)
               || string.Equals(status, Running, StringComparison.OrdinalIgnoreCase)
               || string.Equals(status, Cancelling, StringComparison.OrdinalIgnoreCase);
    }

    public static bool CanRequestCancellation(string status)
    {
        return string.Equals(status, Queued, StringComparison.OrdinalIgnoreCase)
               || string.Equals(status, Running, StringComparison.OrdinalIgnoreCase);
    }
}
