namespace Sudoku.Application.Datasets;

public sealed record CreateDatasetPreparationMlRequestDto(
    string PreparationName,
    IReadOnlyList<CreateDatasetPreparationMlSourceDto> Sources);
