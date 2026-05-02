namespace Sudoku.Application.ModelsRegistry;

public sealed record FinalizeTrainedModelManifestDto(
    string Name,
    string DisplayName,
    string SourceRunName,
    string ParentModelName,
    string TrainingMode,
    string Framework,
    string ArchitectureType,
    string ArchitectureFamily,
    int ArchitectureNumClasses,
    int ArchitectureInputChannels,
    int ArchitectureInputHeight,
    int ArchitectureInputWidth,
    string InputProfile,
    string TrainingProfileName,
    string AugmentationProfileName,
    string PrimaryArtifactRelativePath,
    string ArtifactFormat,
    bool CanUseForInference,
    DateTimeOffset CreatedAtUtc);
