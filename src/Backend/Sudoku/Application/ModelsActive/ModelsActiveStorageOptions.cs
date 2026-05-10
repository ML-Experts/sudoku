using System.ComponentModel.DataAnnotations;

namespace Sudoku.Application.ModelsActive;

public sealed class ModelsActiveStorageOptions
{
    public const string SectionName = "ModelsActiveStorage";

    [Required]
    public string ActiveDirectoryPath { get; init; } = string.Empty;
}
