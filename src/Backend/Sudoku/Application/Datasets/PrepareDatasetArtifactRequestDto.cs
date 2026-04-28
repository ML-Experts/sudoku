namespace Sudoku.Application.Datasets;

public sealed record PrepareDatasetArtifactRequestDto(
    string DatasetName,
    IReadOnlyList<PrepareDatasetSourceDto> Sources,
    string PreprocessingProfile);
