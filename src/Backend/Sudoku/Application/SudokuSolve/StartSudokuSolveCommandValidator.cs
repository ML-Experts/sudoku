using FluentValidation;
using FluentValidation.Results;

namespace Sudoku.Application.SudokuSolve;

public sealed class StartSudokuSolveCommandValidator : AbstractValidator<StartSudokuSolveCommand>
{
    public StartSudokuSolveCommandValidator()
    {
        RuleFor(command => command)
            .Custom((command, context) =>
            {
                if (SudokuGridInputParser.TryParse(
                        command.Grid,
                        out _,
                        out var errorType,
                        out var message))
                {
                    return;
                }

                context.AddFailure(new ValidationFailure(nameof(StartSudokuSolveCommand.Grid), message)
                {
                    ErrorCode = errorType
                });
            });
    }
}
