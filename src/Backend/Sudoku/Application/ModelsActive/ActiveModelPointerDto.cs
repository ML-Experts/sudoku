namespace Sudoku.Application.ModelsActive;

public sealed record ActiveModelPointerDto(
    string ModelName,
    string RegistryRelativePath,
    string SetBy,
    DateTimeOffset UpdatedAtUtc);
