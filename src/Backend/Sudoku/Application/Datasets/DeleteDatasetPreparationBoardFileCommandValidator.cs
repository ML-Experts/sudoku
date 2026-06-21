using FluentValidation;

namespace Sudoku.Application.Datasets;

public sealed class DeleteDatasetPreparationBoardFileCommandValidator
    : AbstractValidator<DeleteDatasetPreparationBoardFileCommand>
{
    public DeleteDatasetPreparationBoardFileCommandValidator()
    {
        RuleFor(command => command.PreparationName)
            .Custom((preparationName, context) => DatasetPreparationNameValidationRules.Validate(
                preparationName,
                context,
                nameof(DeleteDatasetPreparationBoardFileCommand.PreparationName),
                DeleteDatasetPreparationBoardFileErrorTypes.InvalidDatasetPreparationName));

        RuleFor(command => command.SourceName)
            .Custom((sourceName, context) => DatasetPreparationSourceNameValidationRules.Validate(
                sourceName,
                context,
                nameof(DeleteDatasetPreparationBoardFileCommand.SourceName),
                DeleteDatasetPreparationBoardFileErrorTypes.InvalidDatasetPreparationSourceName));

        RuleFor(command => command.BoardFolderName)
            .Custom((boardFolderName, context) => DatasetPreparationBoardFolderNameValidationRules.Validate(
                boardFolderName,
                context,
                nameof(DeleteDatasetPreparationBoardFileCommand.BoardFolderName),
                DeleteDatasetPreparationBoardFileErrorTypes.InvalidDatasetPreparationBoardFolderName));
    }
}
