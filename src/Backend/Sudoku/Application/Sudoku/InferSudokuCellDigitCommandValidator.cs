using FluentValidation;
using FluentValidation.Results;
using Microsoft.Extensions.Options;

namespace Sudoku.Application.Sudoku;

public sealed class InferSudokuCellDigitCommandValidator : AbstractValidator<InferSudokuCellDigitCommand>
{
    private static readonly IReadOnlyCollection<string> AllowedMimeTypes =
        new[] { "image/jpeg", "image/jpg", "image/png" };

    public InferSudokuCellDigitCommandValidator(IOptions<SudokuCellsInferenceOptions> options)
    {
        var inferenceOptions = options.Value;

        RuleFor(command => command)
            .Custom((command, context) =>
            {
                if (string.IsNullOrWhiteSpace(command.MimeType))
                {
                    context.AddFailure(CreateFailure(
                        nameof(InferSudokuCellDigitCommand.MimeType),
                        "Pole 'mimeType' jest wymagane."));
                }
                else if (!AllowedMimeTypes.Contains(command.MimeType, StringComparer.OrdinalIgnoreCase))
                {
                    context.AddFailure(CreateFailure(
                        nameof(InferSudokuCellDigitCommand.MimeType),
                        "Dozwolone są wyłącznie typy MIME obrazu: image/jpeg, image/jpg oraz image/png."));
                }

                if (string.IsNullOrWhiteSpace(command.Base64))
                {
                    context.AddFailure(CreateFailure(
                        nameof(InferSudokuCellDigitCommand.Base64),
                        "Pole 'base64' jest wymagane."));
                    return;
                }

                byte[] decodedContent;
                try
                {
                    decodedContent = Convert.FromBase64String(command.Base64);
                }
                catch (FormatException)
                {
                    context.AddFailure(CreateFailure(
                        nameof(InferSudokuCellDigitCommand.Base64),
                        "Pole 'base64' musi zawierać poprawny ciąg Base64."));
                    return;
                }

                if (decodedContent.Length > inferenceOptions.MaxInlineImageSizeBytes)
                {
                    context.AddFailure(CreateFailure(
                        nameof(InferSudokuCellDigitCommand.Base64),
                        $"Rozmiar obrazu po dekodowaniu przekracza limit {inferenceOptions.MaxInlineImageSizeBytes} bajtów."));
                }
            });
    }

    private static ValidationFailure CreateFailure(string propertyName, string message)
    {
        return new ValidationFailure(propertyName, message)
        {
            ErrorCode = InferSudokuCellDigitErrorTypes.InvalidRequest
        };
    }
}
