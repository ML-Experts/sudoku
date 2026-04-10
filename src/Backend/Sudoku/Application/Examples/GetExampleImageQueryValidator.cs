using FluentValidation;
using FluentValidation.Results;

namespace Sudoku.Application.Examples;

public sealed class GetExampleImageQueryValidator : AbstractValidator<GetExampleImageQuery>
{
    private const int MaxNameLength = 255;

    public GetExampleImageQueryValidator()
    {
        RuleFor(query => query)
            .Custom((query, context) =>
            {
                if (string.IsNullOrWhiteSpace(query.Name))
                {
                    context.AddFailure(CreateFailure(
                        nameof(GetExampleImageQuery.Name),
                        "Parametr ścieżki 'name' jest wymagany."));
                    return;
                }

                if (query.Name.Length > MaxNameLength)
                {
                    context.AddFailure(CreateFailure(
                        nameof(GetExampleImageQuery.Name),
                        $"Parametr 'name' nie może być dłuższy niż {MaxNameLength} znaków."));
                }

                if (query.Name.Contains("..", StringComparison.Ordinal))
                {
                    context.AddFailure(CreateFailure(
                        nameof(GetExampleImageQuery.Name),
                        "Parametr 'name' nie może zawierać sekwencji '..'."));
                }

                if (query.Name.Contains(Path.DirectorySeparatorChar) || query.Name.Contains(Path.AltDirectorySeparatorChar))
                {
                    context.AddFailure(CreateFailure(
                        nameof(GetExampleImageQuery.Name),
                        "Parametr 'name' nie może zawierać separatorów ścieżki."));
                }
            });
    }

    private static ValidationFailure CreateFailure(string propertyName, string message)
    {
        return new ValidationFailure(propertyName, message)
        {
            ErrorCode = GetExampleImageErrorTypes.InvalidRequest
        };
    }
}
