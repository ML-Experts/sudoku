namespace Sudoku.Application.Datasets;

public sealed record PrepareDatasetSourceDto(
    string Name,
    string Type,
    DatasetSplitPolicyDto SplitPolicy);
