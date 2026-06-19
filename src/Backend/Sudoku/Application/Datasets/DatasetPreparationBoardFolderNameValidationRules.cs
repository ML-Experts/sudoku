using FluentValidation;
using FluentValidation.Results;

namespace Sudoku.Application.Datasets;

public static class DatasetPreparationBoardFolderNameValidationRules
{
    private const int MaxBoardFolderNameLength = 160;

    public static void Validate<T>(
        string? boardFolderName,
        ValidationContext<T> context,
        string propertyName,
        string errorCode)
    {
        if (string.IsNullOrWhiteSpace(boardFolderName))
        {
            context.AddFailure(CreateFailure(propertyName, errorCode, "Pole 'boardFolderName' jest wymagane."));
            return;
        }

        var trimmedBoardFolderName = boardFolderName.Trim();
        if (trimmedBoardFolderName.Length > MaxBoardFolderNameLength)
        {
            context.AddFailure(CreateFailure(
                propertyName,
                errorCode,
                $"Pole 'boardFolderName' nie może być dłuższe niż {MaxBoardFolderNameLength} znaków."));
        }

        if (trimmedBoardFolderName.Contains("..", StringComparison.Ordinal)
            || trimmedBoardFolderName.Contains('/', StringComparison.Ordinal)
            || trimmedBoardFolderName.Contains('\\', StringComparison.Ordinal)
            || trimmedBoardFolderName.Contains(':', StringComparison.Ordinal)
            || trimmedBoardFolderName.Any(char.IsControl)
            || trimmedBoardFolderName.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0)
        {
            context.AddFailure(CreateFailure(
                propertyName,
                errorCode,
                "Pole 'boardFolderName' zawiera niedozwolone znaki."));
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
