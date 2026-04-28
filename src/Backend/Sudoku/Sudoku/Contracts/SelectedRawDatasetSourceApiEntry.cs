namespace Sudoku.Contracts;

public sealed record SelectedRawDatasetSourceApiEntry(
    string Name,
    string Type,
    IReadOnlyList<string> Splits);
