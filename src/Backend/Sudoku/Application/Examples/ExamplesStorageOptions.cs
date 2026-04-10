using System.ComponentModel.DataAnnotations;

namespace Sudoku.Application.Examples;

public sealed class ExamplesStorageOptions
{
    public const string SectionName = "ExamplesStorage";

    [Required]
    public string RootPath { get; init; } = "examples";

    [Required]
    public string UploadsSubdirectory { get; init; } = "uploads";
}
