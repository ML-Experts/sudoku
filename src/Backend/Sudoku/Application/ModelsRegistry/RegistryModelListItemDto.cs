namespace Sudoku.Application.ModelsRegistry;

public sealed record RegistryModelListItemDto(
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
    IReadOnlyList<string> Warnings);
