using FluentValidation;
using FluentValidation.Results;

namespace Sudoku.Application.Examples;

public sealed class PreprocessExampleBoardCommandValidator : AbstractValidator<PreprocessExampleBoardCommand>
{
    private const int MaxNameLength = 255;

    public PreprocessExampleBoardCommandValidator()
    {
        RuleFor(command => command)
            .Custom((command, context) =>
            {
                if (string.IsNullOrWhiteSpace(command.Name))
                {
                    context.AddFailure(CreateFailure(
                        nameof(PreprocessExampleBoardCommand.Name),
                        "Parametr ścieżki 'name' jest wymagany."));
                    return;
                }

                if (command.Name.Length > MaxNameLength)
                {
                    context.AddFailure(CreateFailure(
                        nameof(PreprocessExampleBoardCommand.Name),
                        $"Parametr 'name' nie może być dłuższy niż {MaxNameLength} znaków."));
                }

                if (command.Name.Contains("..", StringComparison.Ordinal))
                {
                    context.AddFailure(CreateFailure(
                        nameof(PreprocessExampleBoardCommand.Name),
                        "Parametr 'name' nie może zawierać sekwencji '..'."));
                }

                if (command.Name.Contains(Path.DirectorySeparatorChar) || command.Name.Contains(Path.AltDirectorySeparatorChar))
                {
                    context.AddFailure(CreateFailure(
                        nameof(PreprocessExampleBoardCommand.Name),
                        "Parametr 'name' nie może zawierać separatorów ścieżki."));
                }
            });
    }

    private static ValidationFailure CreateFailure(string propertyName, string message)
    {
        return new ValidationFailure(propertyName, message)
        {
            ErrorCode = PreprocessExampleBoardErrorTypes.InvalidRequest
        };
    }
}
