using Sudoku.Application.Examples;

namespace Application.Tests;

public sealed class InlineImagePayloadValidationRulesTests
{
    [Fact]
    public void Validate_ReturnsError_WhenBase64IsInvalid()
    {
        var failures = InlineImagePayloadValidationRules.Validate(
            mimeType: "image/png",
            base64: "not-base64",
            maxInlineImageSizeBytes: 10,
            mimeTypePropertyName: "MimeType",
            base64PropertyName: "Base64",
            errorCode: "invalid_request");

        var failure = Assert.Single(failures);
        Assert.Equal("invalid_request", failure.ErrorCode);
        Assert.Equal("Base64", failure.PropertyName);
    }

    [Fact]
    public void Validate_ReturnsError_WhenDecodedPayloadExceedsLimit()
    {
        var failures = InlineImagePayloadValidationRules.Validate(
            mimeType: "image/png",
            base64: Convert.ToBase64String([1, 2, 3, 4]),
            maxInlineImageSizeBytes: 3,
            mimeTypePropertyName: "MimeType",
            base64PropertyName: "Base64",
            errorCode: "invalid_request");

        var failure = Assert.Single(failures);
        Assert.Equal("Base64", failure.PropertyName);
    }

    [Fact]
    public void Validate_Succeeds_ForAllowedMimeTypeAndValidBase64()
    {
        var failures = InlineImagePayloadValidationRules.Validate(
            mimeType: "image/jpg",
            base64: Convert.ToBase64String([1, 2, 3]),
            maxInlineImageSizeBytes: 3,
            mimeTypePropertyName: "MimeType",
            base64PropertyName: "Base64",
            errorCode: "invalid_request");

        Assert.Empty(failures);
    }
}
