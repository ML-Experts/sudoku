namespace Sudoku.Realtime;

public static class SudokuSolveHubGroups
{
    public static string ForSolveSession(string solveSessionId)
    {
        return $"sudoku-solve:{solveSessionId}";
    }
}
