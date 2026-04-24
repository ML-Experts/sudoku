namespace Sudoku.Application.Datasets;

public sealed record CreateProcessedDatasetCommandResultDto(
    string Name,
    string FileName,
    string PreprocessingProfile,
    DateTimeOffset CreatedAtUtc,
    IReadOnlyList<SelectedRawDatasetSourceDto> Sources,
    SplitSampleCountsDto SampleCounts,
    IReadOnlyList<ProcessedDatasetSourceReportDto> SourceReports,
    IReadOnlyList<string> Warnings);
