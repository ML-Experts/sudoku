namespace Sudoku.Contracts;

public sealed record DatasetPreparationSourceApiResponse(
    string Name,
    string Type,
    int PreparedItemsCount);
