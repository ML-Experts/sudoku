namespace Sudoku.Application.Sudoku;

public static class InferSudokuCellDigitErrorTypes
{
    public const string InvalidRequest = "invalid_request";
    public const string ActiveModelNotConfigured = "active_model_not_configured";
    public const string ActiveModelPointerInvalid = "active_model_pointer_invalid";
    public const string ActiveModelManifestInvalid = "active_model_manifest_invalid";
    public const string ActiveModelCannotUseForInference = "active_model_cannot_use_for_inference";
    public const string CellImageNotProcessable = "cell_image_not_processable";
    public const string MlInvalidResponse = "ml_invalid_response";
    public const string MlUnavailable = "ml_unavailable";
    public const string MlTimeout = "ml_timeout";
}
