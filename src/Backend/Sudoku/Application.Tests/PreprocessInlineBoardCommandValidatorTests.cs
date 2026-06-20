using Microsoft.Extensions.Options;
using Sudoku.Application.Examples;

namespace Application.Tests;

public sealed class PreprocessInlineBoardCommandValidatorTests
{
    private readonly PreprocessInlineBoardCommandValidator _validator = new(Options.Create(new ExamplesPreprocessOptions
    {
        MaxInlineImageSizeBytes = 4
    }));

    [Fact]
    public void Validate_ReturnsError_WhenMimeTypeIsMissing()
    {
        var result = _validator.Validate(new PreprocessInlineBoardCommand(
            MimeType: " ",
            Base64: Convert.ToBase64String([1, 2, 3])));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(PreprocessInlineBoardErrorTypes.InvalidRequest, failure.ErrorCode);
        Assert.Equal(nameof(PreprocessInlineBoardCommand.MimeType), failure.PropertyName);
    }

    [Fact]
    public void Validate_ReturnsError_WhenMimeTypeIsUnsupported()
    {
        var result = _validator.Validate(new PreprocessInlineBoardCommand(
            MimeType: "image/gif",
            Base64: Convert.ToBase64String([1, 2, 3])));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(PreprocessInlineBoardErrorTypes.InvalidRequest, failure.ErrorCode);
        Assert.Equal(nameof(PreprocessInlineBoardCommand.MimeType), failure.PropertyName);
    }

    [Fact]
    public void Validate_ReturnsError_WhenBase64IsMissing()
    {
        var result = _validator.Validate(new PreprocessInlineBoardCommand(
            MimeType: "image/png",
            Base64: " "));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(PreprocessInlineBoardErrorTypes.InvalidRequest, failure.ErrorCode);
        Assert.Equal(nameof(PreprocessInlineBoardCommand.Base64), failure.PropertyName);
    }

    [Fact]
    public void Validate_ReturnsError_WhenBase64IsInvalid()
    {
        var result = _validator.Validate(new PreprocessInlineBoardCommand(
            MimeType: "image/png",
            Base64: "not-base64"));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(PreprocessInlineBoardErrorTypes.InvalidRequest, failure.ErrorCode);
        Assert.Equal(nameof(PreprocessInlineBoardCommand.Base64), failure.PropertyName);
    }

    [Fact]
    public void Validate_ReturnsError_WhenDecodedPayloadExceedsLimit()
    {
        var result = _validator.Validate(new PreprocessInlineBoardCommand(
            MimeType: "image/png",
            Base64: Convert.ToBase64String([1, 2, 3, 4, 5])));

        var failure = Assert.Single(result.Errors);
        Assert.Equal(PreprocessInlineBoardErrorTypes.InvalidRequest, failure.ErrorCode);
        Assert.Equal(nameof(PreprocessInlineBoardCommand.Base64), failure.PropertyName);
    }

    [Fact]
    public void Validate_Succeeds_ForValidPayload()
    {
        var result = _validator.Validate(new PreprocessInlineBoardCommand(
            MimeType: "image/jpeg",
            Base64: Convert.ToBase64String([1, 2, 3, 4])));

        Assert.True(result.IsValid);
    }
}
