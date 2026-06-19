namespace Sudoku.Application.Datasets;

public sealed record GetDatasetPreparationDetailsQueryResultDto(
    string PreparationName,
    DateTimeOffset CreatedAtUtc,
    string Status,
    IReadOnlyList<DatasetPreparationSourceReportDto> Sources,
    IReadOnlyList<string> Warnings);
