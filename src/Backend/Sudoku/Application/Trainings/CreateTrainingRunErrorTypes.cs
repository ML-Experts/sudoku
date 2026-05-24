namespace Sudoku.Application.Trainings;

public static class CreateTrainingRunErrorTypes
{
    public const string InvalidRequest = "invalid_training_run_request";
    public const string TrainingRunAlreadyActive = "training_run_already_active";
    public const string BaseModelNotFound = "base_model_not_found";
    public const string ProcessedDatasetNotFound = "processed_dataset_not_found";
    public const string BaseModelCannotStartTraining = "base_model_cannot_start_training";
    public const string ProcessedDatasetCannotStartTraining = "processed_dataset_cannot_start_training";
    public const string TrainingProfileMismatch = "training_profile_mismatch";
    public const string MlTrainingStartRejected = "ml_training_start_rejected";
    public const string MlTrainingStartUnavailable = "ml_training_start_unavailable";
    public const string MlTrainingStartTimeout = "ml_training_start_timeout";
    public const string TrainingRunStartFailed = "training_run_start_failed";
    public const string TrainingRunInvariantViolation = "training_run_invariant_violated";
}
