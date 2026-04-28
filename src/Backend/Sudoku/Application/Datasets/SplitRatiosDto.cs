namespace Sudoku.Application.Datasets;

public sealed record SplitRatiosDto(
    double Train,
    double Val,
    double Test);
