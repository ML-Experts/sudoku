using FluentValidation;
using FluentValidation.Results;

namespace Sudoku.Application.Datasets;

public sealed class CreateDatasetPreparationCommandValidator : AbstractValidator<CreateDatasetPreparationCommand>
{
    private static readonly HashSet<string> AllowedTypes = new(StringComparer.OrdinalIgnoreCase)
    {
        "board",
        "digit"
    };

    public CreateDatasetPreparationCommandValidator()
    {
        RuleFor(command => command)
            .Custom((command, context) =>
            {
                ValidatePreparationName(command, context);
                ValidateSources(command, context);
            });
    }

    private static void ValidatePreparationName(
        CreateDatasetPreparationCommand command,
        ValidationContext<CreateDatasetPreparationCommand> context)
    {
        if (string.IsNullOrWhiteSpace(command.PreparationName))
        {
            context.AddFailure(CreateFailure(
                nameof(CreateDatasetPreparationCommand.PreparationName),
                "Pole 'preparationName' jest wymagane."));
            return;
        }

        var trimmedName = command.PreparationName.Trim();
        if (trimmedName.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0
            || trimmedName.Contains('/', StringComparison.Ordinal)
            || trimmedName.Contains('\\', StringComparison.Ordinal))
        {
            context.AddFailure(CreateFailure(
                nameof(CreateDatasetPreparationCommand.PreparationName),
                "Pole 'preparationName' zawiera niedozwolone znaki."));
        }
    }

    private static void ValidateSources(
        CreateDatasetPreparationCommand command,
        ValidationContext<CreateDatasetPreparationCommand> context)
    {
        if (command.Sources is null || command.Sources.Count == 0)
        {
            context.AddFailure(CreateFailure(
                nameof(CreateDatasetPreparationCommand.Sources),
                "Pole 'sources' musi zawierać co najmniej jedno źródło."));
            return;
        }

        var distinctPairs = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        for (var index = 0; index < command.Sources.Count; index++)
        {
            var source = command.Sources[index];
            var propertyPrefix = $"{nameof(CreateDatasetPreparationCommand.Sources)}[{index}]";

            if (string.IsNullOrWhiteSpace(source.Name))
            {
                context.AddFailure(CreateFailure(
                    $"{propertyPrefix}.{nameof(CreateDatasetPreparationSourceDto.Name)}",
                    "Pole 'name' źródła jest wymagane."));
            }

            if (string.IsNullOrWhiteSpace(source.Type) || !AllowedTypes.Contains(source.Type))
            {
                context.AddFailure(CreateFailure(
                    $"{propertyPrefix}.{nameof(CreateDatasetPreparationSourceDto.Type)}",
                    "Pole 'type' źródła musi mieć wartość 'board' albo 'digit'."));
            }

            var sourceName = source.Name?.Trim() ?? string.Empty;
            var sourceType = source.Type?.Trim() ?? string.Empty;
            var sourceKey = $"{sourceName}::{sourceType}";
            if (!string.IsNullOrWhiteSpace(sourceName)
                && !string.IsNullOrWhiteSpace(sourceType)
                && !distinctPairs.Add(sourceKey))
            {
                context.AddFailure(CreateFailure(
                    propertyPrefix,
                    $"Źródło '{sourceName}' typu '{sourceType}' zostało podane więcej niż raz."));
            }
        }
    }

    private static ValidationFailure CreateFailure(string propertyName, string message)
    {
        return new ValidationFailure(propertyName, message)
        {
            ErrorCode = CreateDatasetPreparationErrorTypes.InvalidRequest
        };
    }
}
