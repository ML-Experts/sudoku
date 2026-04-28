namespace Sudoku.Application.Datasets;

public sealed record ListProcessedDatasetsQueryResultDto(
    IReadOnlyList<ProcessedDatasetListItemDto> Items,
    int TotalCount);
