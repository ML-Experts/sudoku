using System.ComponentModel.DataAnnotations;

namespace Sudoku.Infrastructure.Configuration;

public sealed class MlServiceOptions
{
    public const string SectionName = "MlService";

    [Required]
    public string BaseUrl { get; init; } = string.Empty;

    [Required]
    public string PingPath { get; init; } = "/ml/ping";

    [Required]
    public string PreprocessBoardPath { get; init; } = "/ml/preprocess/board";

    [Required]
    public string PreprocessCellsPath { get; init; } = "/ml/preprocess/cells";

    [Range(1, 60)]
    public int TimeoutSeconds { get; init; } = 10;
}
