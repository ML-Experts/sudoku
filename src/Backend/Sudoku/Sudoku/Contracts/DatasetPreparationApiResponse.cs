namespace Sudoku.Contracts;

public sealed record DatasetPreparationApiResponse(
    string PreparationName,
    DateTimeOffset CreatedAtUtc,
    string Status,
    IReadOnlyList<DatasetPreparationSourceApiResponse> Sources,
    IReadOnlyList<string> Warnings);
