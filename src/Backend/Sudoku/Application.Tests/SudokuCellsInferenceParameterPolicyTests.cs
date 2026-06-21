using Sudoku.Application.Sudoku;

namespace Application.Tests;

public sealed class SudokuCellsInferenceParameterPolicyTests
{
    [Fact]
    public void Resolve_UsesRequestValues_WhenAllParametersAreProvided()
    {
        var options = new SudokuCellsInferenceOptions
        {
            InferenceProfileName = "default-28x28-v1",
            EmptyCellInnerMarginRatio = 0.12,
            EmptyCellDarkPixelRatioThreshold = 0.02,
            CenterAreaRatio = 0.5,
            MinComponentAreaRatio = 0.055,
            LineArtifactMinSpanRatio = 0.4,
            LineArtifactMaxThicknessRatio = 0.08,
            EmptyCellMinSegmentLengthPx = 8,
            EmptyCellFilteredSegmentCountThreshold = 2
        };
        var command = new InferSudokuCellDigitCommand(
            MimeType: "image/png",
            Base64: Convert.ToBase64String([1, 2, 3]),
            EmptyCellDarkPixelRatioThreshold: 0.03,
            EmptyCellInnerMarginRatio: 0.11,
            CenterAreaRatio: 0.49,
            MinComponentAreaRatio: 0.02,
            LineArtifactMinSpanRatio: 0.5,
            LineArtifactMaxThicknessRatio: 0.07,
            EmptyCellMinSegmentLengthPx: 10,
            EmptyCellFilteredSegmentCountThreshold: 4);

        var resolved = SudokuCellsInferenceParameterPolicy.Resolve(command, options);

        Assert.Equal("default-28x28-v1", resolved.InferenceProfileName);
        Assert.Equal(0.03, resolved.EmptyCellDarkPixelRatioThreshold);
        Assert.Equal(0.11, resolved.EmptyCellInnerMarginRatio);
        Assert.Equal(0.49, resolved.CenterAreaRatio);
        Assert.Equal(0.02, resolved.MinComponentAreaRatio);
        Assert.Equal(0.5, resolved.LineArtifactMinSpanRatio);
        Assert.Equal(0.07, resolved.LineArtifactMaxThicknessRatio);
        Assert.Equal(10, resolved.EmptyCellMinSegmentLengthPx);
        Assert.Equal(4, resolved.EmptyCellFilteredSegmentCountThreshold);
    }

    [Fact]
    public void Resolve_UsesOptionsFallbacks_WhenParametersAreMissing()
    {
        var options = new SudokuCellsInferenceOptions
        {
            InferenceProfileName = "default-28x28-v1",
            EmptyCellInnerMarginRatio = 0.13,
            EmptyCellDarkPixelRatioThreshold = 0.04,
            CenterAreaRatio = 0.51,
            MinComponentAreaRatio = 0.056,
            LineArtifactMinSpanRatio = 0.41,
            LineArtifactMaxThicknessRatio = 0.09,
            EmptyCellMinSegmentLengthPx = 9,
            EmptyCellFilteredSegmentCountThreshold = 3
        };
        var command = new InferSudokuCellDigitCommand(
            MimeType: "image/png",
            Base64: Convert.ToBase64String([1, 2, 3]),
            EmptyCellDarkPixelRatioThreshold: null,
            EmptyCellInnerMarginRatio: null,
            CenterAreaRatio: null,
            MinComponentAreaRatio: null,
            LineArtifactMinSpanRatio: null,
            LineArtifactMaxThicknessRatio: null,
            EmptyCellMinSegmentLengthPx: null,
            EmptyCellFilteredSegmentCountThreshold: null);

        var resolved = SudokuCellsInferenceParameterPolicy.Resolve(command, options);

        Assert.Equal(0.04, resolved.EmptyCellDarkPixelRatioThreshold);
        Assert.Equal(0.13, resolved.EmptyCellInnerMarginRatio);
        Assert.Equal(0.51, resolved.CenterAreaRatio);
        Assert.Equal(0.056, resolved.MinComponentAreaRatio);
        Assert.Equal(0.41, resolved.LineArtifactMinSpanRatio);
        Assert.Equal(0.09, resolved.LineArtifactMaxThicknessRatio);
        Assert.Equal(9, resolved.EmptyCellMinSegmentLengthPx);
        Assert.Equal(3, resolved.EmptyCellFilteredSegmentCountThreshold);
    }
}
