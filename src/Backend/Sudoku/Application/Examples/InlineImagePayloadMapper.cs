using Sudoku.Models.Images;

namespace Sudoku.Application.Examples;

public static class InlineImagePayloadMapper
{
    public static ImageContent MapToImageContent(string? mimeType, string? base64)
    {
        if (string.IsNullOrWhiteSpace(mimeType) || string.IsNullOrWhiteSpace(base64))
        {
            throw new InvalidOperationException("Inline image payload must be validated before mapping.");
        }

        try
        {
            return new ImageContent(
                MimeType: mimeType,
                Content: Convert.FromBase64String(base64));
        }
        catch (FormatException)
        {
            throw new InvalidOperationException("Inline image payload contains invalid Base64 content.");
        }
    }
}
