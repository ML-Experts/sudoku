namespace Sudoku.Contracts;

public sealed record ProcessedDatasetApiResponse(
    string Name,
    string FileName,
    string PreprocessingProfile,
    DateTimeOffset CreatedAtUtc,
    IReadOnlyList<SelectedRawDatasetSourceApiEntry> Sources,
    SplitSampleCountsApiResponse SampleCounts,
    IReadOnlyList<ProcessedDatasetSourceReportApiResponse> SourceReports,
    IReadOnlyList<string> Warnings);
