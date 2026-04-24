namespace Sudoku.Application.Datasets;

public sealed record PreparedDatasetSourceReportDto(
    string Name,
    string RequestedType,
    string DetectedType,
    int ProcessedSampleCount,
    int IncludedSampleCount,
    int EmptyCellCount,
    int RejectedSampleCount,
    IReadOnlyList<string> Warnings);
