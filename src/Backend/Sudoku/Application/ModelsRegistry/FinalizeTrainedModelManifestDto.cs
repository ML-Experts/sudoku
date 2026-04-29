namespace Sudoku.Application.ModelsRegistry;

public sealed record FinalizeTrainedModelManifestDto(
    string Name,
    string DisplayName,
    string SourceRunName,
    string ParentModelName,
    string TrainingMode,
    string InputProfile,
    string TrainingProfileName,
    string AugmentationProfileName,
    string PrimaryArtifactRelativePath,
    DateTimeOffset CreatedAtUtc);
