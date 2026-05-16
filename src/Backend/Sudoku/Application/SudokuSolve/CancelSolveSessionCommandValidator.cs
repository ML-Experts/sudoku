using FluentValidation;

namespace Sudoku.Application.SudokuSolve;

public sealed class CancelSolveSessionCommandValidator : AbstractValidator<CancelSolveSessionCommand>
{
    public CancelSolveSessionCommandValidator()
    {
        RuleFor(command => command.SolveSessionId)
            .Cascade(CascadeMode.Stop)
            .NotEmpty()
            .WithErrorCode(CancelSolveSessionErrorTypes.InvalidSolveSessionId)
            .WithMessage("Pole solveSessionId jest wymagane.")
            .Must(solveSessionId => !string.IsNullOrWhiteSpace(solveSessionId))
            .WithErrorCode(CancelSolveSessionErrorTypes.InvalidSolveSessionId)
            .WithMessage("Pole solveSessionId nie może być puste.");
    }
}
