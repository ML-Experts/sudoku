namespace Sudoku.Application.Datasets;

public sealed record DatasetPreparationMetadataDto(
    string PreparationName,
    string Status,
    DateTimeOffset CreatedAtUtc,
    IReadOnlyList<CreateDatasetPreparationSourceDto> Sources,
    IReadOnlyList<DatasetPreparationSourceReportDto> SourceReports,
    IReadOnlyList<string> Warnings,
    DateTimeOffset? UpdatedAtUtc = null,
    DateTimeOffset? StartedAtUtc = null,
    DateTimeOffset? FinishedAtUtc = null,
    string? FailureErrorType = null,
    string? FailureMessage = null);
