using FluentValidation;
using FluentValidation.Results;

namespace Sudoku.Application.Trainings;

public sealed class CreateTrainingRunCommandValidator : AbstractValidator<CreateTrainingRunCommand>
{
    private const int MaxNameLength = 128;

    public CreateTrainingRunCommandValidator()
    {
        RuleFor(command => command)
            .Custom((command, context) =>
            {
                ValidateName(command.BaseModelName, nameof(CreateTrainingRunCommand.BaseModelName), context);
                ValidateName(command.ProcessedDatasetName, nameof(CreateTrainingRunCommand.ProcessedDatasetName), context);
            });
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
}
