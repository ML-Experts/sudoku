using FluentValidation.Results;

namespace Sudoku.Application.Examples;

public static class InlineImagePayloadValidationRules
{
    private static readonly IReadOnlyCollection<string> AllowedMimeTypes =
        ["image/jpeg", "image/jpg", "image/png"];

    public static IReadOnlyList<ValidationFailure> Validate(
        string? mimeType,
        string? base64,
        long maxInlineImageSizeBytes,
        string mimeTypePropertyName,
        string base64PropertyName,
        string errorCode)
    {
        var failures = new List<ValidationFailure>();

        if (string.IsNullOrWhiteSpace(mimeType))
        {
            failures.Add(CreateFailure(
                mimeTypePropertyName,
                "Pole 'mimeType' jest wymagane.",
                errorCode));
        }
        else if (!AllowedMimeTypes.Contains(mimeType, StringComparer.OrdinalIgnoreCase))
        {
            failures.Add(CreateFailure(
                mimeTypePropertyName,
                "Dozwolone są wyłącznie typy MIME obrazu: image/jpeg, image/jpg oraz image/png.",
                errorCode));
        }

        if (string.IsNullOrWhiteSpace(base64))
        {
            failures.Add(CreateFailure(
                base64PropertyName,
                "Pole 'base64' jest wymagane.",
                errorCode));
            return failures;
        }

        byte[] decodedContent;
        try
        {
            decodedContent = Convert.FromBase64String(base64);
        }
        catch (FormatException)
        {
            failures.Add(CreateFailure(
                base64PropertyName,
                "Pole 'base64' musi zawierać poprawny ciąg Base64.",
                errorCode));
            return failures;
        }

        if (decodedContent.Length > maxInlineImageSizeBytes)
        {
            failures.Add(CreateFailure(
                base64PropertyName,
                $"Rozmiar obrazu po dekodowaniu przekracza limit {maxInlineImageSizeBytes} bajtów.",
                errorCode));
        }

        return failures;
    }

    private static ValidationFailure CreateFailure(string propertyName, string message, string errorCode)
    {
        return new ValidationFailure(propertyName, message)
        {
            ErrorCode = errorCode
        };
    }
}
