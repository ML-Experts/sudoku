namespace Sudoku.Application.SudokuSolve;

public static class SudokuSolveParameterPolicy
{
    public const int DefaultSolverStepDelayMs = 50;
    public const int MinSolverStepDelayMs = 0;
    public const int MaxSolverStepDelayMs = 2000;

    public static int ResolveSolverStepDelayMs(int? requestedValue)
    {
        if (requestedValue is null)
        {
            return DefaultSolverStepDelayMs;
        }

        return requestedValue.Value < MinSolverStepDelayMs || requestedValue.Value > MaxSolverStepDelayMs
            ? DefaultSolverStepDelayMs
            : requestedValue.Value;
    }
}
