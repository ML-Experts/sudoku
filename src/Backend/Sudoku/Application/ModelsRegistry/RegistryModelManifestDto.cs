namespace Sudoku.Application.ModelsRegistry;

public sealed record RegistryModelManifestDto(
    string Name,
    string DisplayName,
    string SourceType,
    string? SourceRunName,
    string? ParentModelName,
    string TrainingMode,
    string InputProfile,
    string? TrainingProfileName,
    string? AugmentationProfileName,
    DateTimeOffset? CreatedAtUtc,
    bool CanStartTraining,
    bool CanUseForInference,
    string? PrimaryArtifactRelativePath,
    IReadOnlyList<string> Warnings);
