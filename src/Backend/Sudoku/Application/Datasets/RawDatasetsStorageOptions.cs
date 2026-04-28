using System.ComponentModel.DataAnnotations;

namespace Sudoku.Application.Datasets;

public sealed class RawDatasetsStorageOptions
{
    public const string SectionName = "RawDatasetsStorage";

    [Required]
    public string BoardsSubdirectory { get; init; } = string.Empty;

    [Required]
    public string DigitsSubdirectory { get; init; } = string.Empty;
}
