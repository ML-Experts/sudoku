namespace Sudoku.Realtime;

public static class TrainingRunHubGroups
{
    public static string ForRun(string runName)
    {
        return $"training-run:{runName}";
    }
}
