using FluentValidation;

namespace Sudoku.Application.Datasets;

public sealed class GetDatasetPreparationBoardImageQueryValidator
    : AbstractValidator<GetDatasetPreparationBoardImageQuery>
{
    public GetDatasetPreparationBoardImageQueryValidator()
    {
        RuleFor(query => query.PreparationName)
            .Custom((preparationName, context) => DatasetPreparationNameValidationRules.Validate(
                preparationName,
                context,
                nameof(GetDatasetPreparationBoardImageQuery.PreparationName),
                GetDatasetPreparationBoardImageErrorTypes.InvalidDatasetPreparationName));

        RuleFor(query => query.SourceName)
            .Custom((sourceName, context) => DatasetPreparationSourceNameValidationRules.Validate(
                sourceName,
                context,
                nameof(GetDatasetPreparationBoardImageQuery.SourceName),
                GetDatasetPreparationBoardImageErrorTypes.InvalidDatasetPreparationSourceName));

        RuleFor(query => query.BoardFolderName)
            .Custom((boardFolderName, context) => DatasetPreparationBoardFolderNameValidationRules.Validate(
                boardFolderName,
                context,
                nameof(GetDatasetPreparationBoardImageQuery.BoardFolderName),
                GetDatasetPreparationBoardImageErrorTypes.InvalidDatasetPreparationBoardFolderName));
    }
}
