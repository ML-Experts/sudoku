using FluentValidation;

namespace Sudoku.Application.Auth;

public sealed class LoginCommandValidator : AbstractValidator<LoginCommand>
{
    public LoginCommandValidator()
    {
        RuleFor(command => command.Password)
            .NotEmpty()
            .WithErrorCode(AdminAuthErrorTypes.InvalidRequest)
            .WithMessage("Pole 'password' jest wymagane.");
    }
}
