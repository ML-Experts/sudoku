using System.ComponentModel.DataAnnotations;

namespace Sudoku.Application.Trainings;

public sealed class TrainingDefaultsOptions
{
    public const string SectionName = "TrainingDefaults";

    [Required]
    public string RunNamePrefix { get; init; } = "train";

    [Required]
    public string TrainingMode { get; init; } = "fineTuning";

    [Required]
    public string TrainingProfileName { get; init; } = string.Empty;

    [Required]
    public string AugmentationProfileName { get; init; } = string.Empty;

    [Required]
    public string BenchmarkName { get; init; } = string.Empty;

    public int Seed { get; init; } = 1234;
}
