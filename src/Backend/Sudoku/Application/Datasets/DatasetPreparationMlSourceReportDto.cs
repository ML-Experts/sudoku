namespace Sudoku.Application.Datasets;

public sealed record DatasetPreparationMlSourceReportDto(
    string Name,
    string Type,
    int PreparedItemsCount,
    int RejectedItemsCount,
    int EmptyCellCount);
