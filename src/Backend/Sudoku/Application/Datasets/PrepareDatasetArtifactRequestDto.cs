namespace Sudoku.Application.Datasets;

public sealed record PrepareDatasetArtifactRequestDto(
    string PreparationName,
    string DatasetName,
    IReadOnlyList<PrepareDatasetSourceDto> Sources,
    string PreprocessingProfile);
