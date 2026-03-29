using System.ComponentModel.DataAnnotations;

namespace Sudoku.Configuration;

public sealed class BackendRuntimeOptions
{
    public const string SectionName = "Runtime";

    [Required]
    public string Environment { get; init; } = "local";

    [Required]
    public string ServiceName { get; init; } = "sudoku-backend";

    [Required]
    public string ServiceVersion { get; init; } = "0.1.0";
}
