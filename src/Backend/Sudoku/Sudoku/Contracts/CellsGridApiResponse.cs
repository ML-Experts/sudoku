namespace Sudoku.Contracts;

public sealed record CellsGridApiResponse(
    IReadOnlyList<IReadOnlyList<ImageApiResponse>> Cells);
