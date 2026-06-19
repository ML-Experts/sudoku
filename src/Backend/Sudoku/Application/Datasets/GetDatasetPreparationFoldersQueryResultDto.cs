namespace Sudoku.Application.Datasets;

public sealed record GetDatasetPreparationFoldersQueryResultDto(
    string PreparationName,
    string Type,
    IReadOnlyList<string> Items,
    int TotalCount);
