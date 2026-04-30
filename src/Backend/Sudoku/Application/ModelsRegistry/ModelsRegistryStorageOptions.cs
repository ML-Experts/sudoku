using System.ComponentModel.DataAnnotations;

namespace Sudoku.Application.ModelsRegistry;

public sealed class ModelsRegistryStorageOptions
{
    public const string SectionName = "ModelsRegistryStorage";

    [Required]
    public string RegistryDirectoryPath { get; init; } = string.Empty;
}
