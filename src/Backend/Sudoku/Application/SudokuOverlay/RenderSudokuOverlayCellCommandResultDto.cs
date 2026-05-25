namespace Sudoku.Application.SudokuOverlay;

public sealed record RenderSudokuOverlayCellCommandResultDto(
    string MimeType,
    string Base64);
