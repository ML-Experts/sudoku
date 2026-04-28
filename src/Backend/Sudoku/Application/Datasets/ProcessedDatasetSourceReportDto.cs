namespace Sudoku.Application.Datasets;

public sealed record ProcessedDatasetSourceReportDto(
    string Name,
    string Type,
    int ProcessedSampleCount,
    int IncludedSampleCount,
    int EmptyCellCount,
    int RejectedSampleCount,
    IReadOnlyList<string> Warnings);
