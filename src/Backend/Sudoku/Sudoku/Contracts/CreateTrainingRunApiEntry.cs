namespace Sudoku.Contracts;

public sealed record CreateTrainingRunApiEntry(
    string? BaseModelName,
    string? ProcessedDatasetName);
