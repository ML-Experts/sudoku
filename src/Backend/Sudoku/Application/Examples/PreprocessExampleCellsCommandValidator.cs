using FluentValidation;
using Microsoft.Extensions.Options;

namespace Sudoku.Application.Examples;

public sealed class PreprocessExampleCellsCommandValidator : AbstractValidator<PreprocessExampleCellsCommand>
{
    public PreprocessExampleCellsCommandValidator(IOptions<ExamplesPreprocessOptions> options)
    {
        var preprocessOptions = options.Value;

        RuleFor(command => command)
            .Custom((command, context) =>
            {
                var failures = InlineImagePayloadValidationRules.Validate(
                    command.MimeType,
                    command.Base64,
                    preprocessOptions.MaxInlineImageSizeBytes,
                    nameof(PreprocessExampleCellsCommand.MimeType),
                    nameof(PreprocessExampleCellsCommand.Base64),
                    PreprocessExampleCellsErrorTypes.InvalidRequest);

                foreach (var failure in failures)
                {
                    context.AddFailure(failure);
                }
            });
    }
}
