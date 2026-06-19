namespace Sudoku.Application.Datasets;

public sealed record CreateDatasetPreparationCommandResultDto(
    string PreparationName,
    DateTimeOffset CreatedAtUtc,
    string Status,
    IReadOnlyList<DatasetPreparationSourceReportDto> Sources,
    IReadOnlyList<string> Warnings);
