using System.ComponentModel.DataAnnotations;

namespace Sudoku.Configuration;

public sealed class MlServiceOptions
{
    public const string SectionName = "MlService";

    [Required]
    public string BaseUrl { get; init; } = string.Empty;

    [Required]
    public string PingPath { get; init; } = "/ml/ping";

    [Range(1, 60)]
    public int TimeoutSeconds { get; init; } = 10;
}
