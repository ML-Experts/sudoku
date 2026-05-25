using MediatR;

namespace Sudoku.Application.SudokuOverlay;

public sealed record RenderSudokuOverlayCellCommand(
    string? CellImageMimeType,
    string? CellImageBase64,
    int Digit,
    int? RowIndex,
    int? ColumnIndex)
    : IRequest<RenderSudokuOverlayCellCommandResultDto>;
