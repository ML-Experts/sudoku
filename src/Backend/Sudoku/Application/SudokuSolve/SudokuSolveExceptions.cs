namespace Sudoku.Application.SudokuSolve;

public sealed class ActiveSolveSessionAlreadyExistsException : Exception
{
    public ActiveSolveSessionAlreadyExistsException(string activeSolveSessionId)
        : base($"Istnieje już aktywna sesja rozwiązywania sudoku {activeSolveSessionId}.")
    {
        ActiveSolveSessionId = activeSolveSessionId;
    }

    public string ActiveSolveSessionId { get; }
}

public sealed class SudokuGridConflictsException : Exception
{
    public SudokuGridConflictsException(string message)
        : base(message)
    {
    }
}

public sealed class SolveSessionStartException : Exception
{
    public SolveSessionStartException(
        string errorType,
        string message,
        Exception? innerException = null)
        : base(message, innerException)
    {
        ErrorType = errorType;
    }

    public string ErrorType { get; }
}

public sealed class SolveSessionCancelPersistenceException : Exception
{
    public SolveSessionCancelPersistenceException(
        string message,
        Exception? innerException = null)
        : base(message, innerException)
    {
    }
}

public sealed class SolveSessionNotFoundForRealtimeException : Exception
{
    public SolveSessionNotFoundForRealtimeException(string solveSessionId)
        : base($"Nie znaleziono sesji rozwiązywania sudoku {solveSessionId} dla kanału realtime.")
    {
        SolveSessionId = solveSessionId;
    }

    public string SolveSessionId { get; }
}
