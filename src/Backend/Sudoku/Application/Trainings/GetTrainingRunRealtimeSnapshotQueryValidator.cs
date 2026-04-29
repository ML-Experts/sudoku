using FluentValidation;
using FluentValidation.Results;

namespace Sudoku.Application.Trainings;

public sealed class GetTrainingRunRealtimeSnapshotQueryValidator
    : AbstractValidator<GetTrainingRunRealtimeSnapshotQuery>
{
    private const int MaxNameLength = 128;

    public GetTrainingRunRealtimeSnapshotQueryValidator()
    {
        RuleFor(query => query.RunName)
            .Custom(ValidateRunName);
    }

    private static void ValidateRunName(
        string? value,
        ValidationContext<GetTrainingRunRealtimeSnapshotQuery> context)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            context.AddFailure(CreateFailure("Pole jest wymagane."));
            return;
        }

        var trimmedValue = value.Trim();
        if (trimmedValue.Length > MaxNameLength
            || trimmedValue.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0
            || trimmedValue.Contains('/', StringComparison.Ordinal))
        {
            context.AddFailure(CreateFailure("Pole zawiera niedozwoloną nazwę runu."));
        }
    }

    private static ValidationFailure CreateFailure(string message)
    {
        return new ValidationFailure(nameof(GetTrainingRunRealtimeSnapshotQuery.RunName), message)
        {
            ErrorCode = GetTrainingRunRealtimeSnapshotErrorTypes.InvalidRequest
        };
    }
}
