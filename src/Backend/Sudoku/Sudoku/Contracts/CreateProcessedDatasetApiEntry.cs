namespace Sudoku.Contracts;

public sealed record CreateProcessedDatasetApiEntry(
    string? PreparationName,
    string? Name,
    IReadOnlyList<SelectedRawDatasetSourceApiEntry>? Sources);
