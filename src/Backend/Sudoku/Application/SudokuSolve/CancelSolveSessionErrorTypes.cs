namespace Sudoku.Application.SudokuSolve;

public static class CancelSolveSessionErrorTypes
{
    public const string InvalidSolveSessionId = "invalid_solve_session_id";
    public const string SolveSessionCancelPersistenceFailed = "solve_session_cancel_persistence_failed";
    public const string SolveSessionCancelInvariantViolation = "solve_session_cancel_invariant_violation";
}
