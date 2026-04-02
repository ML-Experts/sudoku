using FluentValidation;
using FluentValidation.Results;
using Microsoft.Extensions.Options;

namespace Sudoku.Application.Examples;

public sealed class UploadExampleCommandValidator : AbstractValidator<UploadExampleCommand>
{
    private static readonly IReadOnlyCollection<string> AllowedContentTypes =
        new[] { "image/jpeg", "image/jpg", "image/png" };

    public UploadExampleCommandValidator(IOptions<ExamplesUploadOptions> options)
    {
        var uploadOptions = options.Value;

        RuleFor(command => command)
            .Custom((command, context) =>
            {
                if (command.FileStream is null)
                {
                    context.AddFailure(CreateFailure(
                        nameof(UploadExampleCommand.FileStream),
                        UploadExampleErrorTypes.InvalidRequest,
                        "Pole formularza 'file' jest wymagane."));
                }

                if (!command.SizeBytes.HasValue || command.SizeBytes.Value <= 0)
                {
                    context.AddFailure(CreateFailure(
                        nameof(UploadExampleCommand.SizeBytes),
                        UploadExampleErrorTypes.InvalidRequest,
                        "Plik musi mieć rozmiar większy niż 0 bajtów."));
                }
                else if (command.SizeBytes.Value > uploadOptions.MaxUploadSizeBytes)
                {
                    context.AddFailure(CreateFailure(
                        nameof(UploadExampleCommand.SizeBytes),
                        UploadExampleErrorTypes.PayloadTooLarge,
                        $"Rozmiar pliku przekracza limit {uploadOptions.MaxUploadSizeBytes} bajtów."));
                }

                if (string.IsNullOrWhiteSpace(command.ContentType))
                {
                    context.AddFailure(CreateFailure(
                        nameof(UploadExampleCommand.ContentType),
                        UploadExampleErrorTypes.InvalidRequest,
                        "Nie można ustalić typu MIME przesłanego pliku."));
                }
                else if (!AllowedContentTypes.Contains(command.ContentType, StringComparer.OrdinalIgnoreCase))
                {
                    context.AddFailure(CreateFailure(
                        nameof(UploadExampleCommand.ContentType),
                        UploadExampleErrorTypes.UnsupportedMediaType,
                        "Dozwolone są wyłącznie pliki JPG i PNG."));
                }
            });
    }

    private static ValidationFailure CreateFailure(string propertyName, string errorCode, string message)
    {
        return new ValidationFailure(propertyName, message)
        {
            ErrorCode = errorCode
        };
    }
}
