using Microsoft.Extensions.Options;
using Sudoku.Application.Sudoku;

namespace Application.Tests;

public sealed class InferSudokuCellDigitCommandValidatorTests
{
    private readonly InferSudokuCellDigitCommandValidator _validator = new(Options.Create(new SudokuCellsInferenceOptions
    {
        MaxInlineImageSizeBytes = 8
    }));

    [Fact]
    public void Validate_ReturnsError_WhenEmptyCellInnerMarginRatioIsOutOfRange()
    {
        var result = _validator.Validate(CreateCommand(emptyCellInnerMarginRatio: 0.5));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(InferSudokuCellDigitErrorTypes.InvalidRequest, failure.ErrorCode);
        Assert.Equal(nameof(InferSudokuCellDigitCommand.EmptyCellInnerMarginRatio), failure.PropertyName);
    }

    [Fact]
    public void Validate_ReturnsError_WhenUnitRatioParameterIsOutOfRange()
    {
        var result = _validator.Validate(CreateCommand(centerAreaRatio: 1.1));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(InferSudokuCellDigitErrorTypes.InvalidRequest, failure.ErrorCode);
        Assert.Equal(nameof(InferSudokuCellDigitCommand.CenterAreaRatio), failure.PropertyName);
    }

    [Fact]
    public void Validate_ReturnsError_WhenSegmentLengthIsNotPositive()
    {
        var result = _validator.Validate(CreateCommand(emptyCellMinSegmentLengthPx: 0));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(InferSudokuCellDigitErrorTypes.InvalidRequest, failure.ErrorCode);
        Assert.Equal(nameof(InferSudokuCellDigitCommand.EmptyCellMinSegmentLengthPx), failure.PropertyName);
    }

    [Fact]
    public void Validate_ReturnsError_WhenFilteredSegmentThresholdIsNotPositive()
    {
        var result = _validator.Validate(CreateCommand(emptyCellFilteredSegmentCountThreshold: 0));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(InferSudokuCellDigitErrorTypes.InvalidRequest, failure.ErrorCode);
        Assert.Equal(nameof(InferSudokuCellDigitCommand.EmptyCellFilteredSegmentCountThreshold), failure.PropertyName);
    }

    [Fact]
    public void Validate_Succeeds_WhenFunctionalParametersAreMissing()
    {
        var result = _validator.Validate(CreateCommand(
            emptyCellDarkPixelRatioThreshold: null,
            emptyCellInnerMarginRatio: null,
            centerAreaRatio: null,
            minComponentAreaRatio: null,
            lineArtifactMinSpanRatio: null,
            lineArtifactMaxThicknessRatio: null,
            emptyCellMinSegmentLengthPx: null,
            emptyCellFilteredSegmentCountThreshold: null));

        Assert.True(result.IsValid);
    }

    private static InferSudokuCellDigitCommand CreateCommand(
        double? emptyCellDarkPixelRatioThreshold = 0.02,
        double? emptyCellInnerMarginRatio = 0.12,
        double? centerAreaRatio = 0.5,
        double? minComponentAreaRatio = 0.055,
        double? lineArtifactMinSpanRatio = 0.4,
        double? lineArtifactMaxThicknessRatio = 0.08,
        int? emptyCellMinSegmentLengthPx = 8,
        int? emptyCellFilteredSegmentCountThreshold = 2)
    {
        return new InferSudokuCellDigitCommand(
            MimeType: "image/png",
            Base64: Convert.ToBase64String([1, 2, 3, 4]),
            EmptyCellDarkPixelRatioThreshold: emptyCellDarkPixelRatioThreshold,
            EmptyCellInnerMarginRatio: emptyCellInnerMarginRatio,
            CenterAreaRatio: centerAreaRatio,
            MinComponentAreaRatio: minComponentAreaRatio,
            LineArtifactMinSpanRatio: lineArtifactMinSpanRatio,
            LineArtifactMaxThicknessRatio: lineArtifactMaxThicknessRatio,
            EmptyCellMinSegmentLengthPx: emptyCellMinSegmentLengthPx,
            EmptyCellFilteredSegmentCountThreshold: emptyCellFilteredSegmentCountThreshold);
    }
}
