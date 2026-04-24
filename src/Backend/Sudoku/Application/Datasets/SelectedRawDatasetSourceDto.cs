namespace Sudoku.Application.Datasets;

public sealed record SelectedRawDatasetSourceDto(
    string Name,
    string Type,
    IReadOnlyList<string> Splits);
