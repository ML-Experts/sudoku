namespace Sudoku.Contracts;

public sealed record DatasetPreparationFoldersApiResponse(
    string PreparationName,
    string Type,
    IReadOnlyList<string> Items,
    int TotalCount);
