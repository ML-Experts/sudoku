namespace Sudoku.Application.Datasets;

public sealed record PrepareDatasetArtifactResultDto(
    SplitSampleCountsDto SampleCounts,
    IReadOnlyList<PreparedDatasetSourceReportDto> Sources,
    IReadOnlyList<string> Warnings);
