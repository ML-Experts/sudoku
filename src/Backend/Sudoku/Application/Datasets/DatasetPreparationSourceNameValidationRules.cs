using FluentValidation;
using FluentValidation.Results;

namespace Sudoku.Application.Datasets;

public static class DatasetPreparationSourceNameValidationRules
{
    private const int MaxSourceNameLength = 160;

    public static void Validate<T>(
        string? sourceName,
        ValidationContext<T> context,
        string propertyName,
        string errorCode)
    {
        if (string.IsNullOrWhiteSpace(sourceName))
        {
            context.AddFailure(CreateFailure(propertyName, errorCode, "Pole 'sourceName' jest wymagane."));
            return;
        }

        var trimmedSourceName = sourceName.Trim();
        if (trimmedSourceName.Length > MaxSourceNameLength)
        {
            context.AddFailure(CreateFailure(
                propertyName,
                errorCode,
                $"Pole 'sourceName' nie może być dłuższe niż {MaxSourceNameLength} znaków."));
        }

        if (trimmedSourceName.Contains("..", StringComparison.Ordinal)
            || trimmedSourceName.Contains('/', StringComparison.Ordinal)
            || trimmedSourceName.Contains('\\', StringComparison.Ordinal)
            || trimmedSourceName.Contains(':', StringComparison.Ordinal)
            || trimmedSourceName.Any(char.IsControl)
            || trimmedSourceName.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0)
        {
            context.AddFailure(CreateFailure(
                propertyName,
                errorCode,
                "Pole 'sourceName' zawiera niedozwolone znaki."));
        }
    }

    private static ValidationFailure CreateFailure(string propertyName, string errorCode, string message)
    {
        return new ValidationFailure(propertyName, message)
        {
            ErrorCode = errorCode
        };
    }
}
