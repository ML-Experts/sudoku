namespace Sudoku.Application.ModelsActive;

public static class GetActiveModelErrorTypes
{
    public const string PointerInvalid = "active_model_pointer_invalid";
    public const string ReadFailed = "active_model_read_failed";
    public const string CannotUseForInference = SetActiveModelErrorTypes.CannotUseForInference;
    public const string ManifestInvalid = SetActiveModelErrorTypes.ManifestInvalid;
}
