namespace Sudoku.Application.Datasets;

public sealed record DatasetSplitPolicyDto(
    string Mode,
    SplitRatiosDto Ratios,
    string GroupBy);
