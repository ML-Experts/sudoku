using FluentValidation;
using FluentValidation.Results;
using Microsoft.Extensions.Options;

namespace Sudoku.Application.SudokuOverlay;

public sealed class RenderSudokuOverlayCellCommandValidator
    : AbstractValidator<RenderSudokuOverlayCellCommand>
{
    private static readonly IReadOnlyCollection<string> AllowedMimeTypes =
        ["image/jpeg", "image/jpg", "image/png"];

    public RenderSudokuOverlayCellCommandValidator(IOptions<SudokuOverlayOptions> options)
    {
        var overlayOptions = options.Value;

        RuleFor(command => command)
            .Custom((command, context) =>
            {
                if (string.IsNullOrWhiteSpace(command.CellImageMimeType))
                {
                    context.AddFailure(CreateFailure(
                        nameof(RenderSudokuOverlayCellCommand.CellImageMimeType),
                        "Pole 'cellImage.mimeType' jest wymagane.",
                        RenderSudokuOverlayCellErrorTypes.InvalidRequest));
                }
                else if (!AllowedMimeTypes.Contains(command.CellImageMimeType, StringComparer.OrdinalIgnoreCase))
                {
                    context.AddFailure(CreateFailure(
                        nameof(RenderSudokuOverlayCellCommand.CellImageMimeType),
                        "Dozwolone są wyłącznie typy MIME obrazu: image/jpeg, image/jpg oraz image/png.",
                        RenderSudokuOverlayCellErrorTypes.InvalidRequest));
                }

                if (string.IsNullOrWhiteSpace(command.CellImageBase64))
                {
                    context.AddFailure(CreateFailure(
                        nameof(RenderSudokuOverlayCellCommand.CellImageBase64),
                        "Pole 'cellImage.base64' jest wymagane.",
                        RenderSudokuOverlayCellErrorTypes.InvalidRequest));
                }
                else
                {
                    byte[] decodedContent;
                    try
                    {
                        decodedContent = Convert.FromBase64String(command.CellImageBase64);
                    }
                    catch (FormatException)
                    {
                        context.AddFailure(CreateFailure(
                            nameof(RenderSudokuOverlayCellCommand.CellImageBase64),
                            "Pole 'cellImage.base64' musi zawierać poprawny ciąg Base64.",
                            RenderSudokuOverlayCellErrorTypes.InvalidRequest));
                        return;
                    }

                    if (decodedContent.Length > overlayOptions.MaxInlineCellImageSizeBytes)
                    {
                        context.AddFailure(CreateFailure(
                            nameof(RenderSudokuOverlayCellCommand.CellImageBase64),
                            $"Rozmiar obrazu po dekodowaniu przekracza limit {overlayOptions.MaxInlineCellImageSizeBytes} bajtów.",
                            RenderSudokuOverlayCellErrorTypes.CellImageTooLarge));
                    }
                }

                if (command.Digit is < 1 or > 9)
                {
                    context.AddFailure(CreateFailure(
                        nameof(RenderSudokuOverlayCellCommand.Digit),
                        "Pole 'digit' musi zawierać wartość z zakresu 1..9.",
                        RenderSudokuOverlayCellErrorTypes.DigitOutOfRange));
                }

                var rowProvided = command.RowIndex.HasValue;
                var columnProvided = command.ColumnIndex.HasValue;
                if (rowProvided != columnProvided)
                {
                    context.AddFailure(CreateFailure(
                        nameof(RenderSudokuOverlayCellCommand.RowIndex),
                        "Pola 'rowIndex' i 'columnIndex' muszą zostać podane razem albo pominięte razem.",
                        RenderSudokuOverlayCellErrorTypes.CellPositionInvalid));
                    return;
                }

                if (command.RowIndex is < 0 or > 8)
                {
                    context.AddFailure(CreateFailure(
                        nameof(RenderSudokuOverlayCellCommand.RowIndex),
                        "Pole 'rowIndex' musi mieścić się w zakresie 0..8.",
                        RenderSudokuOverlayCellErrorTypes.CellPositionInvalid));
                }

                if (command.ColumnIndex is < 0 or > 8)
                {
                    context.AddFailure(CreateFailure(
                        nameof(RenderSudokuOverlayCellCommand.ColumnIndex),
                        "Pole 'columnIndex' musi mieścić się w zakresie 0..8.",
                        RenderSudokuOverlayCellErrorTypes.CellPositionInvalid));
                }
            });
    }

    private static ValidationFailure CreateFailure(string propertyName, string message, string errorCode)
    {
        return new ValidationFailure(propertyName, message)
        {
            ErrorCode = errorCode
        };
    }
}
