using FluentValidation;
using FluentValidation.Results;

namespace Sudoku.Application.Datasets;

public static class DatasetPreparationNameValidationRules
{
    private const int MaxPreparationNameLength = 160;

    public static void Validate<T>(
        string? preparationName,
        ValidationContext<T> context,
        string propertyName,
        string errorCode)
    {
        if (string.IsNullOrWhiteSpace(preparationName))
        {
            context.AddFailure(CreateFailure(propertyName, errorCode, "Pole 'preparationName' jest wymagane."));
            return;
        }

        var trimmedPreparationName = preparationName.Trim();
        if (trimmedPreparationName.Length > MaxPreparationNameLength)
        {
            context.AddFailure(CreateFailure(
                propertyName,
                errorCode,
                $"Pole 'preparationName' nie może być dłuższe niż {MaxPreparationNameLength} znaków."));
        }

        if (trimmedPreparationName.Contains("..", StringComparison.Ordinal)
            || trimmedPreparationName.Contains('/', StringComparison.Ordinal)
            || trimmedPreparationName.Contains('\\', StringComparison.Ordinal)
            || trimmedPreparationName.Contains(':', StringComparison.Ordinal)
            || trimmedPreparationName.Any(char.IsControl)
            || trimmedPreparationName.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0)
        {
            context.AddFailure(CreateFailure(
                propertyName,
                errorCode,
                "Pole 'preparationName' zawiera niedozwolone znaki."));
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
