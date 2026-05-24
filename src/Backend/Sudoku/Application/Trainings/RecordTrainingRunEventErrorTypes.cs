namespace Sudoku.Application.Trainings;

public static class RecordTrainingRunEventErrorTypes
{
    public const string InvalidRequest = "training_run_event_invalid";
    public const string TrainingRunNotFound = "training_run_not_found";
    public const string TrainingRunEventConflict = "training_run_event_conflict";
    public const string TrainingRunArtifactNotReady = "training_run_artifact_not_ready";
    public const string TrainingRunEventPersistFailed = "training_run_event_persist_failed";
    public const string TrainingRunEventInvalidTransition = "training_run_event_invalid_transition";
}
