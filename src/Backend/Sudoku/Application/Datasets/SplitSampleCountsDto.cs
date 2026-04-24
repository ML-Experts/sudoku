namespace Sudoku.Application.Datasets;

public sealed record SplitSampleCountsDto(
    int Train,
    int Val,
    int Test);
