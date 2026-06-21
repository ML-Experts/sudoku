namespace Sudoku.Application.Datasets;

public sealed record CreateDatasetPreparationMlResultDto(
    string PreparationName,
    DateTimeOffset? CreatedAtUtc,
    string? Status,
    IReadOnlyList<DatasetPreparationMlSourceReportDto> SourceReports,
    IReadOnlyList<string> Warnings);
