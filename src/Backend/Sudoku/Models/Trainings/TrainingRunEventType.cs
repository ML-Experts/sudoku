namespace Sudoku.Models.Trainings;

public static class TrainingRunEventType
{
    public const string Progress = "progress";
    public const string StatusChanged = "statusChanged";
    public const string Completed = "completed";
    public const string Failed = "failed";
    public const string Cancelled = "cancelled";
}
