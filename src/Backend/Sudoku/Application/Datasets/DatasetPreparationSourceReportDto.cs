namespace Sudoku.Application.Datasets;

public sealed record DatasetPreparationSourceReportDto(
    string Name,
    string Type,
    int PreparedItemsCount,
    int RejectedItemsCount,
    int EmptyCellCount);
