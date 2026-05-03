using FluentValidation;

namespace Sudoku.Application.ModelsActive;

public sealed class SetActiveModelCommandValidator : AbstractValidator<SetActiveModelCommand>
{
    public SetActiveModelCommandValidator()
    {
        RuleFor(command => command.ModelName)
            .Custom(ValidateModelName);
    }

    private static void ValidateModelName(
        string? modelName,
        ValidationContext<SetActiveModelCommand> context)
    {
        var failure = ActiveModelActivationRules.ValidateModelName(
            modelName,
            nameof(SetActiveModelCommand.ModelName));
        if (failure is not null)
        {
            context.AddFailure(failure);
        }
    }
}
