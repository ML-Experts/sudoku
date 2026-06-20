using FluentValidation;
using FluentValidation.Results;

namespace Sudoku.Application.Datasets;

public sealed class CreateProcessedDatasetCommandValidator : AbstractValidator<CreateProcessedDatasetCommand>
{
    private static readonly HashSet<string> AllowedTypes = new(StringComparer.OrdinalIgnoreCase)
    {
        "board",
        "digit"
    };

    private static readonly HashSet<string> AllowedSplits = new(StringComparer.OrdinalIgnoreCase)
    {
        "train",
        "val",
        "test",
        "mix"
    };

    public CreateProcessedDatasetCommandValidator()
    {
        RuleFor(command => command)
            .Custom((command, context) =>
            {
                ValidatePreparationName(command, context);
                ValidateName(command, context);
                ValidateSources(command, context);
            });
    }

    private static void ValidatePreparationName(
        CreateProcessedDatasetCommand command,
        ValidationContext<CreateProcessedDatasetCommand> context)
    {
        DatasetPreparationNameValidationRules.Validate(
            command.PreparationName,
            context,
            nameof(CreateProcessedDatasetCommand.PreparationName),
            CreateProcessedDatasetErrorTypes.InvalidDatasetPreparationName);
    }

    private static void ValidateName(CreateProcessedDatasetCommand command, ValidationContext<CreateProcessedDatasetCommand> context)
    {
        if (string.IsNullOrWhiteSpace(command.Name))
        {
            context.AddFailure(CreateFailure(
                nameof(CreateProcessedDatasetCommand.Name),
                CreateProcessedDatasetErrorTypes.InvalidRequest,
                "Pole 'name' jest wymagane."));
            return;
        }

        var trimmedName = command.Name.Trim();
        if (trimmedName.EndsWith(".npz", StringComparison.OrdinalIgnoreCase))
        {
            context.AddFailure(CreateFailure(
                nameof(CreateProcessedDatasetCommand.Name),
                CreateProcessedDatasetErrorTypes.InvalidRequest,
                "Pole 'name' nie może zawierać rozszerzenia .npz."));
        }

        if (trimmedName.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0 || trimmedName.Contains('/', StringComparison.Ordinal))
        {
            context.AddFailure(CreateFailure(
                nameof(CreateProcessedDatasetCommand.Name),
                CreateProcessedDatasetErrorTypes.InvalidRequest,
                "Pole 'name' zawiera niedozwolone znaki."));
        }
    }

    private static void ValidateSources(
        CreateProcessedDatasetCommand command,
        ValidationContext<CreateProcessedDatasetCommand> context)
    {
        if (command.Sources is null || command.Sources.Count == 0)
        {
            context.AddFailure(CreateFailure(
                nameof(CreateProcessedDatasetCommand.Sources),
                CreateProcessedDatasetErrorTypes.InvalidRequest,
                "Pole 'sources' musi zawierać co najmniej jedno źródło."));
            return;
        }

        var distinctPairs = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        for (var index = 0; index < command.Sources.Count; index++)
        {
            var source = command.Sources[index];
            var propertyPrefix = $"{nameof(CreateProcessedDatasetCommand.Sources)}[{index}]";

            if (string.IsNullOrWhiteSpace(source.Name))
            {
                context.AddFailure(CreateFailure(
                    $"{propertyPrefix}.{nameof(SelectedRawDatasetSourceDto.Name)}",
                    CreateProcessedDatasetErrorTypes.InvalidRequest,
                    "Pole 'name' źródła jest wymagane."));
            }

            if (string.IsNullOrWhiteSpace(source.Type) || !AllowedTypes.Contains(source.Type))
            {
                context.AddFailure(CreateFailure(
                    $"{propertyPrefix}.{nameof(SelectedRawDatasetSourceDto.Type)}",
                    CreateProcessedDatasetErrorTypes.InvalidRequest,
                    "Pole 'type' źródła musi mieć wartość 'board' albo 'digit'."));
            }

            var sourceName = source.Name?.Trim() ?? string.Empty;
            var sourceType = source.Type?.Trim() ?? string.Empty;
            var sourceKey = $"{sourceName}::{sourceType}";
            if (!string.IsNullOrWhiteSpace(sourceName) && !string.IsNullOrWhiteSpace(sourceType) && !distinctPairs.Add(sourceKey))
            {
                context.AddFailure(CreateFailure(
                    propertyPrefix,
                    CreateProcessedDatasetErrorTypes.InvalidRequest,
                    $"Źródło '{sourceName}' typu '{sourceType}' zostało podane więcej niż raz."));
            }

            if (source.Splits is null || source.Splits.Count == 0)
            {
                context.AddFailure(CreateFailure(
                    $"{propertyPrefix}.{nameof(SelectedRawDatasetSourceDto.Splits)}",
                    CreateProcessedDatasetErrorTypes.InvalidDatasetSplitSelection,
                    "Pole 'splits' musi zawierać co najmniej jedną wartość."));
                continue;
            }

            var normalizedSplits = source.Splits
                .Where(split => !string.IsNullOrWhiteSpace(split))
                .Select(split => split.Trim().ToLowerInvariant())
                .Distinct(StringComparer.Ordinal)
                .ToArray();

            if (normalizedSplits.Length != source.Splits.Count || normalizedSplits.Any(split => !AllowedSplits.Contains(split)))
            {
                context.AddFailure(CreateFailure(
                    $"{propertyPrefix}.{nameof(SelectedRawDatasetSourceDto.Splits)}",
                    CreateProcessedDatasetErrorTypes.InvalidDatasetSplitSelection,
                    "Pole 'splits' może zawierać wyłącznie: train, val, test albo mix."));
                continue;
            }

            if (normalizedSplits.Contains("mix", StringComparer.Ordinal) && normalizedSplits.Length > 1)
            {
                context.AddFailure(CreateFailure(
                    $"{propertyPrefix}.{nameof(SelectedRawDatasetSourceDto.Splits)}",
                    CreateProcessedDatasetErrorTypes.InvalidDatasetSplitSelection,
                    "Pole splits dla pojedynczego źródła musi zawierać albo tylko mix, albo jeden lub wiele splitów train/val/test."));
            }
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
