namespace Sudoku.Contracts;

public sealed record SplitSampleCountsApiResponse(
    int Train,
    int Val,
    int Test);
