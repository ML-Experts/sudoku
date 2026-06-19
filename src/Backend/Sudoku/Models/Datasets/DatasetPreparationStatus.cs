namespace Sudoku.Models.Datasets;

public static class DatasetPreparationStatus
{
    public const string Queued = "queued";
    public const string Running = "running";
    public const string Completed = "completed";
    public const string Failed = "failed";

    public static bool IsTerminal(string status)
    {
        return string.Equals(status, Completed, StringComparison.OrdinalIgnoreCase)
               || string.Equals(status, Failed, StringComparison.OrdinalIgnoreCase);
    }
}
