using FluentValidation;
using FluentValidation.Results;

namespace Sudoku.Application.Datasets;

public sealed class GetDatasetPreparationDetailsQueryValidator
    : AbstractValidator<GetDatasetPreparationDetailsQuery>
{
    private const int MaxPreparationNameLength = 160;

    public GetDatasetPreparationDetailsQueryValidator()
    {
        RuleFor(query => query.PreparationName)
            .Custom(ValidatePreparationName);
    }

    private static void ValidatePreparationName(
        string? preparationName,
        ValidationContext<GetDatasetPreparationDetailsQuery> context)
    {
        if (string.IsNullOrWhiteSpace(preparationName))
        {
            context.AddFailure(CreateFailure("Pole 'preparationName' jest wymagane."));
            return;
        }

        var trimmedPreparationName = preparationName.Trim();
        if (trimmedPreparationName.Length > MaxPreparationNameLength)
        {
            context.AddFailure(CreateFailure(
                $"Pole 'preparationName' nie może być dłuższe niż {MaxPreparationNameLength} znaków."));
        }

        if (trimmedPreparationName.Contains("..", StringComparison.Ordinal)
            || trimmedPreparationName.Contains('/', StringComparison.Ordinal)
            || trimmedPreparationName.Contains('\\', StringComparison.Ordinal)
            || trimmedPreparationName.Contains(':', StringComparison.Ordinal)
            || trimmedPreparationName.Any(char.IsControl)
            || trimmedPreparationName.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0)
        {
            context.AddFailure(CreateFailure("Pole 'preparationName' zawiera niedozwolone znaki."));
        }
    }

    private static ValidationFailure CreateFailure(string message)
    {
        return new ValidationFailure(nameof(GetDatasetPreparationDetailsQuery.PreparationName), message)
        {
            ErrorCode = GetDatasetPreparationDetailsErrorTypes.InvalidDatasetPreparationName
        };
    }
}
