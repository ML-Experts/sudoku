using FluentValidation;
using FluentValidation.Results;

namespace Sudoku.Application.Trainings;

public sealed class CreateTrainingRunCommandValidator : AbstractValidator<CreateTrainingRunCommand>
{
    private const int MaxNameLength = 128;
    private static readonly HashSet<string> SupportedFineTuningPolicies = new(StringComparer.Ordinal)
    {
        "all",
        "head-only"
    };

    public CreateTrainingRunCommandValidator()
    {
        RuleFor(command => command)
            .Custom((command, context) =>
            {
                ValidateName(command.BaseModelName, nameof(CreateTrainingRunCommand.BaseModelName), context);
                ValidateName(command.ProcessedDatasetName, nameof(CreateTrainingRunCommand.ProcessedDatasetName), context);
                ValidateTrainingParameters(command.TrainingParameters, context);
            });
    }

    private static void ValidateTrainingParameters(
        TrainingRunRequestedParametersDto? trainingParameters,
        ValidationContext<CreateTrainingRunCommand> context)
    {
        if (trainingParameters is null)
        {
            context.AddFailure(CreateFailure(
                nameof(CreateTrainingRunCommand.TrainingParameters),
                "Pole jest wymagane."));
            return;
        }

        ValidatePositiveInt(
            trainingParameters.Epochs,
            $"{nameof(CreateTrainingRunCommand.TrainingParameters)}.{nameof(TrainingRunRequestedParametersDto.Epochs)}",
            context);
        ValidatePositiveDouble(
            trainingParameters.LearningRate,
            $"{nameof(CreateTrainingRunCommand.TrainingParameters)}.{nameof(TrainingRunRequestedParametersDto.LearningRate)}",
            context,
            maxValue: 1d);
        ValidatePositiveInt(
            trainingParameters.BatchSize,
            $"{nameof(CreateTrainingRunCommand.TrainingParameters)}.{nameof(TrainingRunRequestedParametersDto.BatchSize)}",
            context);
        ValidatePositiveInt(
            trainingParameters.EarlyStoppingPatience,
            $"{nameof(CreateTrainingRunCommand.TrainingParameters)}.{nameof(TrainingRunRequestedParametersDto.EarlyStoppingPatience)}",
            context);
        ValidatePositiveInt(
            trainingParameters.LrSchedulerPatience,
            $"{nameof(CreateTrainingRunCommand.TrainingParameters)}.{nameof(TrainingRunRequestedParametersDto.LrSchedulerPatience)}",
            context);
        ValidatePositiveDouble(
            trainingParameters.LrSchedulerFactor,
            $"{nameof(CreateTrainingRunCommand.TrainingParameters)}.{nameof(TrainingRunRequestedParametersDto.LrSchedulerFactor)}",
            context,
            maxExclusive: 1d);
        ValidateFineTuningPolicy(
            trainingParameters.FineTuningPolicy,
            $"{nameof(CreateTrainingRunCommand.TrainingParameters)}.{nameof(TrainingRunRequestedParametersDto.FineTuningPolicy)}",
            context);
    }

    private static void ValidateName(
        string? value,
        string propertyName,
        ValidationContext<CreateTrainingRunCommand> context)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            context.AddFailure(CreateFailure(
                propertyName,
                "Pole jest wymagane."));
            return;
        }

        var trimmedValue = value.Trim();
        if (trimmedValue.Length > MaxNameLength)
        {
            context.AddFailure(CreateFailure(
                propertyName,
                $"Pole nie może być dłuższe niż {MaxNameLength} znaków."));
        }

        if (trimmedValue.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0
            || trimmedValue.Contains('/', StringComparison.Ordinal))
        {
            context.AddFailure(CreateFailure(
                propertyName,
                "Pole zawiera niedozwolone znaki."));
        }
    }

    private static ValidationFailure CreateFailure(string propertyName, string message)
    {
        return new ValidationFailure(propertyName, message)
        {
            ErrorCode = CreateTrainingRunErrorTypes.InvalidRequest
        };
    }

    private static void ValidatePositiveInt(
        int? value,
        string propertyName,
        ValidationContext<CreateTrainingRunCommand> context)
    {
        if (!value.HasValue)
        {
            context.AddFailure(CreateFailure(propertyName, "Pole jest wymagane."));
            return;
        }

        if (value.Value <= 0)
        {
            context.AddFailure(CreateFailure(propertyName, "Pole musi być większe od zera."));
        }
    }

    private static void ValidatePositiveDouble(
        double? value,
        string propertyName,
        ValidationContext<CreateTrainingRunCommand> context,
        double? maxValue = null,
        double? maxExclusive = null)
    {
        if (!value.HasValue)
        {
            context.AddFailure(CreateFailure(propertyName, "Pole jest wymagane."));
            return;
        }

        if (value.Value <= 0)
        {
            context.AddFailure(CreateFailure(propertyName, "Pole musi być większe od zera."));
            return;
        }

        if (maxValue.HasValue && value.Value > maxValue.Value)
        {
            context.AddFailure(CreateFailure(
                propertyName,
                $"Pole musi być mniejsze lub równe {maxValue.Value}."));
        }

        if (maxExclusive.HasValue && value.Value >= maxExclusive.Value)
        {
            context.AddFailure(CreateFailure(
                propertyName,
                $"Pole musi być mniejsze niż {maxExclusive.Value}."));
        }
    }

    private static void ValidateFineTuningPolicy(
        string? value,
        string propertyName,
        ValidationContext<CreateTrainingRunCommand> context)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            context.AddFailure(CreateFailure(propertyName, "Pole jest wymagane."));
            return;
        }

        var normalizedValue = value.Trim().ToLowerInvariant();
        if (!SupportedFineTuningPolicies.Contains(normalizedValue))
        {
            context.AddFailure(CreateFailure(
                propertyName,
                "Pole zawiera nieobsługiwaną politykę fine-tuningu."));
        }
    }
}
