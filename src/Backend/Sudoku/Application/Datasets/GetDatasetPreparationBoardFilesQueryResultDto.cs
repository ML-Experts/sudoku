namespace Sudoku.Application.Datasets;

public sealed record GetDatasetPreparationBoardFilesQueryResultDto(
    string PreparationName,
    string SourceName,
    IReadOnlyList<DatasetPreparationBoardFileListItemDto> Items,
    int Page,
    int PageSize,
    int TotalCount);
