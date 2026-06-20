namespace Sudoku.Application.Datasets;

public static class CreateProcessedDatasetErrorTypes
{
    public const string InvalidRequest = "invalid_request";
    public const string InvalidDatasetPreparationName = "invalid_dataset_preparation_name";
    public const string InvalidDatasetSplitSelection = "invalid_dataset_split_selection";
    public const string DatasetPreparationNotFound = "dataset_preparation_not_found";
    public const string DatasetPreparationArtifactsNotReady = "dataset_preparation_artifacts_not_ready";
    public const string DatasetPreparationSourceNotFound = "dataset_preparation_source_not_found";
    public const string ProcessedDatasetNameConflict = "processed_dataset_name_conflict";
    public const string DatasetSourceInvalid = "dataset_source_invalid";
    public const string NoSamplesPrepared = "no_samples_prepared";
    public const string MlUnavailable = "ml_unavailable";
    public const string MlTimeout = "ml_timeout";
    public const string ArtifactPromotionFailed = "processed_dataset_artifact_promotion_failed";
}
