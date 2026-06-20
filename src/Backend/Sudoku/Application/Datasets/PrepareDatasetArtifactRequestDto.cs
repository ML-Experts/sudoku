namespace Sudoku.Application.Datasets;

public sealed record PrepareDatasetArtifactRequestDto(
    string PreparationName,
    string DatasetName,
    DatasetSplitPolicyDto SplitPolicy,
    IReadOnlyList<PrepareDatasetSourceDto> Sources);
