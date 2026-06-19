namespace Sudoku.Application.Datasets;

public static class GetDatasetPreparationBoardImageErrorTypes
{
    public const string InvalidDatasetPreparationName = "invalid_dataset_preparation_name";
    public const string InvalidDatasetPreparationSourceName = "invalid_dataset_preparation_source_name";
    public const string InvalidDatasetPreparationBoardFolderName = "invalid_dataset_preparation_board_folder_name";
    public const string DatasetPreparationNotFound = "dataset_preparation_not_found";
    public const string DatasetPreparationSourceNotFound = "dataset_preparation_source_not_found";
    public const string DatasetPreparationBoardFileNotFound = "dataset_preparation_board_file_not_found";
    public const string DatasetPreparationArtifactsNotReady = "dataset_preparation_artifacts_not_ready";
    public const string DatasetPreparationBoardImageReadFailed = "dataset_preparation_board_image_read_failed";
}
