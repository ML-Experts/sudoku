using FluentValidation;
using FluentValidation.Results;

namespace Sudoku.Application.Datasets;

public sealed class GetDatasetPreparationBoardFilesQueryValidator
    : AbstractValidator<GetDatasetPreparationBoardFilesQuery>
{
    public const int MaxPageSize = 200;

    public GetDatasetPreparationBoardFilesQueryValidator()
    {
        RuleFor(query => query.PreparationName)
            .Custom((preparationName, context) => DatasetPreparationNameValidationRules.Validate(
                preparationName,
                context,
                nameof(GetDatasetPreparationBoardFilesQuery.PreparationName),
                GetDatasetPreparationBoardFilesErrorTypes.InvalidDatasetPreparationName));

        RuleFor(query => query.SourceName)
            .Custom((sourceName, context) => DatasetPreparationSourceNameValidationRules.Validate(
                sourceName,
                context,
                nameof(GetDatasetPreparationBoardFilesQuery.SourceName),
                GetDatasetPreparationBoardFilesErrorTypes.InvalidDatasetPreparationSourceName));

        RuleFor(query => query.Page)
            .Custom(ValidatePage);

        RuleFor(query => query.PageSize)
            .Custom(ValidatePageSize);
    }

    private static void ValidatePage(
        int? page,
        ValidationContext<GetDatasetPreparationBoardFilesQuery> context)
    {
        if (!page.HasValue || page.Value < 1)
        {
            context.AddFailure(CreateFailure(
                nameof(GetDatasetPreparationBoardFilesQuery.Page),
                GetDatasetPreparationBoardFilesErrorTypes.InvalidDatasetPreparationBoardFilesPage,
                "Parametr 'page' musi być większy lub równy 1."));
        }
    }

    private static void ValidatePageSize(
        int? pageSize,
        ValidationContext<GetDatasetPreparationBoardFilesQuery> context)
    {
        if (!pageSize.HasValue || pageSize.Value < 1)
        {
            context.AddFailure(CreateFailure(
                nameof(GetDatasetPreparationBoardFilesQuery.PageSize),
                GetDatasetPreparationBoardFilesErrorTypes.InvalidDatasetPreparationBoardFilesPageSize,
                "Parametr 'pageSize' musi być większy lub równy 1."));
            return;
        }

        if (pageSize.Value > MaxPageSize)
        {
            context.AddFailure(CreateFailure(
                nameof(GetDatasetPreparationBoardFilesQuery.PageSize),
                GetDatasetPreparationBoardFilesErrorTypes.InvalidDatasetPreparationBoardFilesPageSize,
                $"Parametr 'pageSize' nie może być większy niż {MaxPageSize}."));
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
