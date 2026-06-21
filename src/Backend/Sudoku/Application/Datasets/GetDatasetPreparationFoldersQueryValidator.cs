using FluentValidation;
using FluentValidation.Results;

namespace Sudoku.Application.Datasets;

public sealed class GetDatasetPreparationFoldersQueryValidator
    : AbstractValidator<GetDatasetPreparationFoldersQuery>
{
    public GetDatasetPreparationFoldersQueryValidator()
    {
        RuleFor(query => query.PreparationName)
            .Custom((preparationName, context) => DatasetPreparationNameValidationRules.Validate(
                preparationName,
                context,
                nameof(GetDatasetPreparationFoldersQuery.PreparationName),
                GetDatasetPreparationFoldersErrorTypes.InvalidDatasetPreparationName));

        RuleFor(query => query.Type)
            .Custom(ValidateType);
    }

    private static void ValidateType(
        string? type,
        ValidationContext<GetDatasetPreparationFoldersQuery> context)
    {
        if (string.IsNullOrWhiteSpace(type))
        {
            context.AddFailure(CreateTypeFailure("Pole 'type' jest wymagane."));
            return;
        }

        var trimmedType = type.Trim();
        if (!string.Equals(trimmedType, "board", StringComparison.OrdinalIgnoreCase)
            && !string.Equals(trimmedType, "digit", StringComparison.OrdinalIgnoreCase))
        {
            context.AddFailure(CreateTypeFailure("Pole 'type' musi mieć wartość 'board' albo 'digit'."));
        }
    }

    private static ValidationFailure CreateTypeFailure(string message)
    {
        return new ValidationFailure(nameof(GetDatasetPreparationFoldersQuery.Type), message)
        {
            ErrorCode = GetDatasetPreparationFoldersErrorTypes.InvalidDatasetPreparationType
        };
    }
}
