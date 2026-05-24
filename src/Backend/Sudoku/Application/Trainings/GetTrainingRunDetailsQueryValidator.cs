using FluentValidation;
using FluentValidation.Results;

namespace Sudoku.Application.Trainings;

public sealed class GetTrainingRunDetailsQueryValidator : AbstractValidator<GetTrainingRunDetailsQuery>
{
    private const int MaxRunNameLength = 160;

    public GetTrainingRunDetailsQueryValidator()
    {
        RuleFor(query => query.RunName)
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

                if (trimmedRunName.Contains("..", StringComparison.Ordinal)
                    || trimmedRunName.Contains('/', StringComparison.Ordinal)
                    || trimmedRunName.Contains('\\', StringComparison.Ordinal)
                    || trimmedRunName.Contains(':', StringComparison.Ordinal)
                    || trimmedRunName.Any(char.IsControl)
                    || trimmedRunName.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0)
                {
                    context.AddFailure(CreateFailure("Nazwa runu zawiera niedozwolone znaki."));
                }
            });
    }

    private static ValidationFailure CreateFailure(string message)
    {
        return new ValidationFailure(nameof(GetTrainingRunDetailsQuery.RunName), message)
        {
            ErrorCode = GetTrainingRunDetailsErrorTypes.InvalidTrainingRunName
        };
    }
}
