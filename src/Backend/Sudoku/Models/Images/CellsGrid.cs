namespace Sudoku.Models.Images;

public sealed record CellsGrid(
    IReadOnlyList<IReadOnlyList<ImageContent>> Cells);
