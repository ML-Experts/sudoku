namespace Sudoku.Contracts;

public sealed record ProcessedDatasetListItemApiResponse(
    string Name,
    string FileName,
    string PreprocessingProfile,
    DateTimeOffset CreatedAtUtc,
    SplitSampleCountsApiResponse SampleCounts);
