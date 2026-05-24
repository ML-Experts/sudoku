namespace Sudoku.Application.SudokuSolve;

public sealed class SolveSessionIdGenerator : ISolveSessionIdGenerator
{
    public string Generate(
        DateTimeOffset createdAtUtc,
        int attempt)
    {
        var timestamp = createdAtUtc.UtcDateTime.ToString("yyyyMMdd-HHmmss");
        return $"solve-{timestamp}-sudoku-{attempt + 1:D2}";
    }
}
