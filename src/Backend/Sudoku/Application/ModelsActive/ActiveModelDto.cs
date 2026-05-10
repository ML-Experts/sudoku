namespace Sudoku.Application.ModelsActive;

public sealed record ActiveModelDto(
    string ModelName,
    string DisplayName,
    string SourceType,
    string? SourceRunName,
    string? ParentModelName,
    string InputProfile,
    bool CanUseForInference,
    DateTimeOffset ActivatedAtUtc);
