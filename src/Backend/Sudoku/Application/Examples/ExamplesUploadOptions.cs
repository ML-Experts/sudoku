using System.ComponentModel.DataAnnotations;

namespace Sudoku.Application.Examples;

public sealed class ExamplesUploadOptions
{
    public const string SectionName = "ExamplesUpload";

    [Range(1, long.MaxValue)]
    public long MaxUploadSizeBytes { get; init; } = 10 * 1024 * 1024;
}
