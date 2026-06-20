using System.ComponentModel.DataAnnotations;

namespace Sudoku.Application.Sudoku;

public sealed class SudokuCellsInferenceOptions
{
    public const string SectionName = "SudokuCellsInference";

    [Range(1, int.MaxValue)]
    public int MaxInlineImageSizeBytes { get; init; } = 10 * 1024 * 1024;

    [Required]
    public string InferenceProfileName { get; init; } = "default-28x28-v1";

    [Range(typeof(double), "0", "1")]
    public double EmptyCellInnerMarginRatio { get; init; } = 0.12d;

    [Range(typeof(double), "0", "1")]
    public double EmptyCellDarkPixelRatioThreshold { get; init; } = 0.02d;

    [Range(typeof(double), "0", "1")]
    public double CenterAreaRatio { get; init; } = 0.5d;

    [Range(typeof(double), "0", "1")]
    public double MinComponentAreaRatio { get; init; } = 0.055d;

    [Range(typeof(double), "0", "1")]
    public double LineArtifactMinSpanRatio { get; init; } = 0.4d;

    [Range(typeof(double), "0", "1")]
    public double LineArtifactMaxThicknessRatio { get; init; } = 0.08d;

    [Range(1, int.MaxValue)]
    public int EmptyCellMinSegmentLengthPx { get; init; } = 8;

    [Range(1, int.MaxValue)]
    public int EmptyCellFilteredSegmentCountThreshold { get; init; } = 2;
}
