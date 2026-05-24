namespace Sudoku.Application.SudokuSolve;

public static class SolveSudokuErrorTypes
{
    public const string InvalidRequest = "invalid_request";
    public const string SolveSessionAlreadyActive = "solve_session_already_active";
    public const string GridValueOutOfRange = "grid_value_out_of_range";
    public const string GridShapeInvalid = "grid_shape_invalid";
    public const string GridConflictsWithSudokuRules = "grid_conflicts_with_sudoku_rules";
    public const string SolveSessionPersistenceFailed = "solve_session_persistence_failed";
    public const string SolveSessionEnqueueFailed = "solve_session_enqueue_failed";
    public const string SolveSessionInvariantViolation = "solve_session_invariant_violation";
    public const string Unsolvable = "unsolvable";
    public const string SolveExecutionFailed = "solve_execution_failed";
}
