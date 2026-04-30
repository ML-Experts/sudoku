namespace Sudoku.Contracts;

public sealed record RegistryModelListItemApiResponse(
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
