namespace Sudoku.Application.Datasets;

public static class CreateDatasetPreparationErrorTypes
{
    public const string InvalidRequest = "invalid_dataset_preparation_request";
    public const string RawDatasetNotFound = "raw_dataset_not_found";
    public const string RawDatasetTypeMismatch = "raw_dataset_type_mismatch";
    public const string PreparationNameConflict = "dataset_preparation_name_conflict";
    public const string PreparationStartFailed = "dataset_preparation_start_failed";
    public const string MlUnavailable = "ml_unavailable";
    public const string MlTimeout = "ml_timeout";
    public const string PreparationFailed = "dataset_preparation_failed";
    public const string PreparationInvariantViolation = "dataset_preparation_invariant_violated";
    public const string PreparationCleanupPartial = "preparation_cleanup_partial";
    public const string PreparationInterrupted = "preparation_interrupted";
}
