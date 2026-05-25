using Sudoku.Models.Images;
using Sudoku.Models.Sudoku;

namespace Sudoku.Application.SudokuOverlay;

public sealed record RenderSudokuOverlayCellMlRequestDto(
    ImageContent CellImage,
    int Digit,
    SudokuCellPosition? CellPosition);
