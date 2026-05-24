using FluentValidation;
using FluentValidation.Results;

namespace Sudoku.Application.Trainings;

public sealed class CancelTrainingRunCommandValidator : AbstractValidator<CancelTrainingRunCommand>
{
    private const int MaxRunNameLength = 160;

    public CancelTrainingRunCommandValidator()
    {
        RuleFor(command => command.RunName)
            .Custom((runName, context) =>
            {
                if (string.IsNullOrWhiteSpace(runName))
                {
                    context.AddFailure(CreateFailure("Nazwa runu jest wymagana."));
                    return;
                }

                var trimmedRunName = runName.Trim();
                if (trimmedRunName.Length > MaxRunNameLength)
                {
                    context.AddFailure(CreateFailure(
                        $"Nazwa runu nie może być dłuższa niż {MaxRunNameLength} znaków."));
                }

                if (trimmedRunName.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0
                    || trimmedRunName.Contains('/', StringComparison.Ordinal))
                {
                    context.AddFailure(CreateFailure("Nazwa runu zawiera niedozwolone znaki."));
                }
            });
    }

    private static ValidationFailure CreateFailure(string message)
    {
        return new ValidationFailure(nameof(CancelTrainingRunCommand.RunName), message)
        {
            ErrorCode = CancelTrainingRunErrorTypes.InvalidTrainingRunName
        };
    }
}
