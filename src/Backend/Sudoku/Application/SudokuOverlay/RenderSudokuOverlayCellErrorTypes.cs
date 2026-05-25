namespace Sudoku.Application.SudokuOverlay;

public static class RenderSudokuOverlayCellErrorTypes
{
    public const string InvalidRequest = "invalid_request";
    public const string DigitOutOfRange = "digit_out_of_range";
    public const string CellImageTooLarge = "cell_image_too_large";
    public const string CellPositionInvalid = "cell_position_invalid";
    public const string CellImageNotProcessable = "cell_image_not_processable";
    public const string OverlayRenderNotPossible = "overlay_render_not_possible";
    public const string MlInvalidResponse = "ml_invalid_response";
    public const string MlUnavailable = "ml_unavailable";
    public const string MlTimeout = "ml_timeout";
    public const string InternalServerError = "internal_server_error";
}
