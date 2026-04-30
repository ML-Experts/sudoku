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

    [Required]
    public string PrepareDatasetPath { get; init; } = "/ml/datasets/prepare";

    [Required]
    public string StartTrainingPath { get; init; } = "/ml/trainings";

    [Required]
    public string CancelTrainingPathTemplate { get; init; } = "/ml/trainings/{runName}/cancel";

    [Required]
    public string TrainingEventsPathTemplate { get; init; } = "/internal/ml/trainings/{runName}/events";

    [Range(1, 600)]
    public int TimeoutSeconds { get; init; } = 60;
}
