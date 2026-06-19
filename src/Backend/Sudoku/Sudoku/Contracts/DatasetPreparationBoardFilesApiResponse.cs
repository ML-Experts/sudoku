namespace Sudoku.Contracts;

public sealed record DatasetPreparationBoardFilesApiResponse(
    string PreparationName,
    string SourceName,
    IReadOnlyList<DatasetPreparationBoardFileListItemApiResponse> Items,
    int Page,
    int PageSize,
    int TotalCount);
