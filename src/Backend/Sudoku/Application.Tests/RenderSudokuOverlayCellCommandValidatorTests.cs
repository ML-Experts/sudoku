using Microsoft.Extensions.Options;
using Sudoku.Application.SudokuOverlay;

namespace Application.Tests;

public sealed class RenderSudokuOverlayCellCommandValidatorTests
{
    private readonly RenderSudokuOverlayCellCommandValidator _validator = new(
        Options.Create(new SudokuOverlayOptions
        {
            MaxInlineCellImageSizeBytes = 4
        }));

    [Fact]
    public void Validate_ReturnsNoErrors_ForValidRequestWithoutPosition()
    {
        var result = _validator.Validate(CreateCommand());

        Assert.True(result.IsValid);
    }

    [Fact]
    public void Validate_ReturnsNoErrors_ForValidRequestWithPosition()
    {
        var result = _validator.Validate(CreateCommand(rowIndex: 0, columnIndex: 2));

        Assert.True(result.IsValid);
    }

    [Fact]
    public void Validate_ReturnsInvalidRequest_WhenBase64IsInvalid()
    {
        var result = _validator.Validate(CreateCommand(cellImageBase64: "not-base64"));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(RenderSudokuOverlayCellErrorTypes.InvalidRequest, failure.ErrorCode);
        Assert.Equal("CellImageBase64", failure.PropertyName);
    }

    [Fact]
    public void Validate_ReturnsDigitOutOfRange_WhenDigitIsOutsideAllowedRange()
    {
        var result = _validator.Validate(CreateCommand(digit: 0));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(RenderSudokuOverlayCellErrorTypes.DigitOutOfRange, failure.ErrorCode);
        Assert.Equal("Digit", failure.PropertyName);
    }

    [Fact]
    public void Validate_ReturnsCellPositionInvalid_WhenOnlyOneCoordinateIsProvided()
    {
        var result = _validator.Validate(CreateCommand(rowIndex: 1, columnIndex: null));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(RenderSudokuOverlayCellErrorTypes.CellPositionInvalid, failure.ErrorCode);
        Assert.Equal("RowIndex", failure.PropertyName);
    }

    [Fact]
    public void Validate_ReturnsCellImageTooLarge_WhenImageExceedsConfiguredLimit()
    {
        var result = _validator.Validate(CreateCommand(cellImageBase64: Convert.ToBase64String([1, 2, 3, 4, 5])));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(RenderSudokuOverlayCellErrorTypes.CellImageTooLarge, failure.ErrorCode);
        Assert.Equal("CellImageBase64", failure.PropertyName);
    }

    private static RenderSudokuOverlayCellCommand CreateCommand(
        string? cellImageMimeType = "image/png",
        string? cellImageBase64 = null,
        int digit = 4,
        int? rowIndex = null,
        int? columnIndex = null)
    {
        return new RenderSudokuOverlayCellCommand(
            CellImageMimeType: cellImageMimeType,
            CellImageBase64: cellImageBase64 ?? Convert.ToBase64String([1, 2, 3, 4]),
            Digit: digit,
            RowIndex: rowIndex,
            ColumnIndex: columnIndex);
    }
}
