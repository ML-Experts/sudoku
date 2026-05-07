namespace Sudoku.Contracts;

public sealed record ActiveModelApiResponse(
    string ModelName,
    string DisplayName,
    string SourceType,
    string? SourceRunName,
    string? ParentModelName,
    string InputProfile,
    bool CanUseForInference,
    DateTimeOffset ActivatedAtUtc);
