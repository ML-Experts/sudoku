namespace Sudoku.Application.Datasets;

public sealed record ListDatasetPreparationsQueryResultDto(
    IReadOnlyList<DatasetPreparationListItemDto> Items,
    int TotalCount);
