namespace Sudoku.Contracts;

public sealed record CreateProcessedDatasetApiEntry(
    string? Name,
    IReadOnlyList<SelectedRawDatasetSourceApiEntry>? Sources);
