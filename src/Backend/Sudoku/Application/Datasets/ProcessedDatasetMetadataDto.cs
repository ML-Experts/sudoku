namespace Sudoku.Application.Datasets;

public sealed record ProcessedDatasetMetadataDto(
    string Name,
    string PreparationName,
    string FileName,
    string PreprocessingProfile,
    DateTimeOffset CreatedAtUtc,
    IReadOnlyList<SelectedRawDatasetSourceDto> Sources,
    SplitSampleCountsDto SampleCounts,
    IReadOnlyList<ProcessedDatasetSourceReportDto> SourceReports,
    IReadOnlyList<string> Warnings);
