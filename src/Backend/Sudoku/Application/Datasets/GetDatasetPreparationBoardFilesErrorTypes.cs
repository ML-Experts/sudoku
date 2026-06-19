namespace Sudoku.Application.Datasets;

public static class GetDatasetPreparationBoardFilesErrorTypes
{
    public const string InvalidDatasetPreparationName = "invalid_dataset_preparation_name";
    public const string InvalidDatasetPreparationSourceName = "invalid_dataset_preparation_source_name";
    public const string InvalidDatasetPreparationBoardFilesPage = "invalid_dataset_preparation_board_files_page";
    public const string InvalidDatasetPreparationBoardFilesPageSize = "invalid_dataset_preparation_board_files_page_size";
    public const string DatasetPreparationNotFound = "dataset_preparation_not_found";
    public const string DatasetPreparationSourceNotFound = "dataset_preparation_source_not_found";
    public const string DatasetPreparationArtifactsNotReady = "dataset_preparation_artifacts_not_ready";
    public const string DatasetPreparationBoardFilesReadFailed = "dataset_preparation_board_files_read_failed";
}
