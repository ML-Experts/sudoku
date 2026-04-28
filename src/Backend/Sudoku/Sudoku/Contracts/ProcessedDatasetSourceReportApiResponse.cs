namespace Sudoku.Contracts;

public sealed record ProcessedDatasetSourceReportApiResponse(
    string Name,
    string Type,
    int ProcessedSampleCount,
    int IncludedSampleCount,
    int EmptyCellCount,
    int RejectedSampleCount,
    IReadOnlyList<string> Warnings);
