using FluentValidation;
namespace Sudoku.Application.Datasets;

public sealed class GetDatasetPreparationDetailsQueryValidator
    : AbstractValidator<GetDatasetPreparationDetailsQuery>
{
    public GetDatasetPreparationDetailsQueryValidator()
    {
        RuleFor(query => query.PreparationName)
            .Custom((preparationName, context) => DatasetPreparationNameValidationRules.Validate(
                preparationName,
                context,
                nameof(GetDatasetPreparationDetailsQuery.PreparationName),
                GetDatasetPreparationDetailsErrorTypes.InvalidDatasetPreparationName));
    }
}
