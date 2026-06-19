namespace Sudoku.Contracts;

public sealed record CreateDatasetPreparationApiEntry(
    string? PreparationName,
    IReadOnlyList<CreateDatasetPreparationSourceApiEntry>? Sources);
