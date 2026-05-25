namespace Sudoku.Contracts;

public sealed record RenderSudokuOverlayCellApiEntry(
    ImageApiEntry? CellImage,
    int Digit,
    int? RowIndex,
    int? ColumnIndex);
