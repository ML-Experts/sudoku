using System.ComponentModel.DataAnnotations;

namespace Sudoku.Application.Examples;

public sealed class ExamplesPreprocessOptions
{
    public const string SectionName = "ExamplesPreprocess";

    [Range(1, long.MaxValue)]
    public long MaxInlineImageSizeBytes { get; init; } = 10 * 1024 * 1024;
}
