namespace Sudoku.Application.Datasets;

public sealed record DatasetPreparationListItemDto(
    string PreparationName,
    DateTimeOffset CreatedAtUtc,
    string Status,
    int BoardSourcesCount,
    int DigitSourcesCount);
