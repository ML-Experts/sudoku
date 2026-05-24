namespace Sudoku.Application.Trainings;

public static class CancelTrainingRunErrorTypes
{
    public const string InvalidTrainingRunName = "invalid_training_run_name";
    public const string MlRejected = "training_cancel_ml_rejected";
    public const string MlUnavailable = "training_cancel_ml_unavailable";
    public const string MlTimeout = "training_cancel_ml_timeout";
    public const string PersistenceFailed = "training_cancel_persistence_failed";
    public const string InvariantViolation = "training_cancel_invariant_violation";
}
