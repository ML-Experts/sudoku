using System.ComponentModel.DataAnnotations;

namespace Sudoku.Application.Examples;

public sealed class ExamplesUploadOptions
{
    public const string SectionName = "ExamplesStorage";

    [Required]
    public string RootPath { get; init; } = "examples";

    [Required]
    public string UploadsSubdirectory { get; init; } = "uploads";

    [Range(1, long.MaxValue)]
    public long MaxUploadSizeBytes { get; init; } = 10 * 1024 * 1024;
}
