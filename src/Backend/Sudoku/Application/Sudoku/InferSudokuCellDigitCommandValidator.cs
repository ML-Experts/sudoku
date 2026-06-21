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

        RuleFor(command => command.EmptyCellInnerMarginRatio)
            .Must(SudokuCellsInferenceParameterPolicy.IsInnerMarginRatioValid)
            .WithMessage("Pole 'emptyCellInnerMarginRatio' musi mieścić się w zakresie [0.0, 0.5).")
            .WithErrorCode(InferSudokuCellDigitErrorTypes.InvalidRequest);

        RuleFor(command => command.EmptyCellDarkPixelRatioThreshold)
            .Must(SudokuCellsInferenceParameterPolicy.IsUnitRatioValid)
            .WithMessage("Pole 'emptyCellDarkPixelRatioThreshold' musi mieścić się w zakresie [0.0, 1.0].")
            .WithErrorCode(InferSudokuCellDigitErrorTypes.InvalidRequest);

        RuleFor(command => command.CenterAreaRatio)
            .Must(SudokuCellsInferenceParameterPolicy.IsUnitRatioValid)
            .WithMessage("Pole 'centerAreaRatio' musi mieścić się w zakresie [0.0, 1.0].")
            .WithErrorCode(InferSudokuCellDigitErrorTypes.InvalidRequest);

        RuleFor(command => command.MinComponentAreaRatio)
            .Must(SudokuCellsInferenceParameterPolicy.IsUnitRatioValid)
            .WithMessage("Pole 'minComponentAreaRatio' musi mieścić się w zakresie [0.0, 1.0].")
            .WithErrorCode(InferSudokuCellDigitErrorTypes.InvalidRequest);

        RuleFor(command => command.LineArtifactMinSpanRatio)
            .Must(SudokuCellsInferenceParameterPolicy.IsUnitRatioValid)
            .WithMessage("Pole 'lineArtifactMinSpanRatio' musi mieścić się w zakresie [0.0, 1.0].")
            .WithErrorCode(InferSudokuCellDigitErrorTypes.InvalidRequest);

        RuleFor(command => command.LineArtifactMaxThicknessRatio)
            .Must(SudokuCellsInferenceParameterPolicy.IsUnitRatioValid)
            .WithMessage("Pole 'lineArtifactMaxThicknessRatio' musi mieścić się w zakresie [0.0, 1.0].")
            .WithErrorCode(InferSudokuCellDigitErrorTypes.InvalidRequest);

        RuleFor(command => command.EmptyCellMinSegmentLengthPx)
            .Must(SudokuCellsInferenceParameterPolicy.IsPositiveInt)
            .WithMessage("Pole 'emptyCellMinSegmentLengthPx' musi być większe od 0.")
            .WithErrorCode(InferSudokuCellDigitErrorTypes.InvalidRequest);

        RuleFor(command => command.EmptyCellFilteredSegmentCountThreshold)
            .Must(SudokuCellsInferenceParameterPolicy.IsPositiveInt)
            .WithMessage("Pole 'emptyCellFilteredSegmentCountThreshold' musi być większe od 0.")
            .WithErrorCode(InferSudokuCellDigitErrorTypes.InvalidRequest);
    }

    private static ValidationFailure CreateFailure(string propertyName, string message)
    {
        return new ValidationFailure(propertyName, message)
        {
            ErrorCode = InferSudokuCellDigitErrorTypes.InvalidRequest
        };
    }
}
