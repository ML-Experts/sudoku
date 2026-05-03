namespace Sudoku.Application.ModelsActive;

public static class SetActiveModelErrorTypes
{
    public const string InvalidRequest = "invalid_request";
    public const string NotFound = "model_not_found";
    public const string CannotUseForInference = "model_cannot_use_for_inference";
    public const string ManifestInvalid = "model_manifest_invalid";
    public const string PointerWriteFailed = "active_model_pointer_write_failed";
}
