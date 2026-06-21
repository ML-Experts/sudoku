namespace Sudoku.Contracts;

public sealed record DatasetPreparationListItemApiResponse(
    string PreparationName,
    DateTimeOffset CreatedAtUtc,
    string Status,
    int BoardSourcesCount,
    int DigitSourcesCount);
