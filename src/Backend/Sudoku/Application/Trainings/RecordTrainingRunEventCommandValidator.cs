using FluentValidation;
using FluentValidation.Results;
using Sudoku.Models.Trainings;

namespace Sudoku.Application.Trainings;

public sealed class RecordTrainingRunEventCommandValidator : AbstractValidator<RecordTrainingRunEventCommand>
{
    private const int MaxNameLength = 128;

    private static readonly HashSet<string> AllowedEventTypes = new(StringComparer.Ordinal)
    {
        TrainingRunEventType.Progress,
        TrainingRunEventType.StatusChanged,
        TrainingRunEventType.Completed,
        TrainingRunEventType.Failed,
        TrainingRunEventType.Cancelled
    };

    private static readonly HashSet<string> AllowedStatuses = new(StringComparer.Ordinal)
    {
        TrainingRunStatus.Queued,
        TrainingRunStatus.Running,
        TrainingRunStatus.Cancelling,
        TrainingRunStatus.Succeeded,
        TrainingRunStatus.Failed,
        TrainingRunStatus.Cancelled
    };

    public RecordTrainingRunEventCommandValidator()
    {
        RuleFor(command => command)
            .Custom((command, context) =>
            {
                ValidateRunName(command.RunName, context);
                ValidateSequence(command.Sequence, context);
                ValidateOccurredAtUtc(command.OccurredAtUtc, context);
                ValidateKnownValue(command.EventType, nameof(command.EventType), AllowedEventTypes, context);
                ValidateKnownValue(command.Status, nameof(command.Status), AllowedStatuses, context);
                ValidateProgress(command.Progress, context);
            });
    }

    private static void ValidateRunName(
        string? value,
        ValidationContext<RecordTrainingRunEventCommand> context)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            context.AddFailure(CreateFailure(nameof(RecordTrainingRunEventCommand.RunName), "Pole jest wymagane."));
            return;
        }

        var trimmedValue = value.Trim();
        if (trimmedValue.Length > MaxNameLength
            || trimmedValue.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0
            || trimmedValue.Contains('/', StringComparison.Ordinal))
        {
            context.AddFailure(CreateFailure(
                nameof(RecordTrainingRunEventCommand.RunName),
                "Pole zawiera niedozwoloną nazwę runu."));
        }
    }

    private static void ValidateSequence(
        long sequence,
        ValidationContext<RecordTrainingRunEventCommand> context)
    {
        if (sequence < 1)
        {
            context.AddFailure(CreateFailure(
                nameof(RecordTrainingRunEventCommand.Sequence),
                "Sequence musi być większe lub równe 1."));
        }
    }

    private static void ValidateKnownValue(
        string? value,
        string propertyName,
        ISet<string> allowedValues,
        ValidationContext<RecordTrainingRunEventCommand> context)
    {
        if (string.IsNullOrWhiteSpace(value) || !allowedValues.Contains(value.Trim()))
        {
            context.AddFailure(CreateFailure(propertyName, "Pole ma niedozwoloną wartość."));
        }
    }

    private static void ValidateOccurredAtUtc(
        DateTimeOffset occurredAtUtc,
        ValidationContext<RecordTrainingRunEventCommand> context)
    {
        if (occurredAtUtc == default)
        {
            context.AddFailure(CreateFailure(
                nameof(RecordTrainingRunEventCommand.OccurredAtUtc),
                "OccurredAtUtc jest wymagane."));
        }
    }

    private static void ValidateProgress(
        TrainingRunProgressDto? progress,
        ValidationContext<RecordTrainingRunEventCommand> context)
    {
        if (progress?.Percent is < 0m or > 100m)
        {
            context.AddFailure(CreateFailure(
                nameof(RecordTrainingRunEventCommand.Progress),
                "Percent musi być w zakresie 0..100."));
        }
    }

    private static ValidationFailure CreateFailure(string propertyName, string message)
    {
        return new ValidationFailure(propertyName, message)
        {
            ErrorCode = RecordTrainingRunEventErrorTypes.InvalidRequest
        };
    }
}
