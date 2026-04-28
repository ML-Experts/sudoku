namespace Sudoku.Application.Datasets;

public sealed record ProcessedDatasetListItemDto(
    string Name,
    string FileName,
    string PreprocessingProfile,
    DateTimeOffset CreatedAtUtc,
    SplitSampleCountsDto SampleCounts);
