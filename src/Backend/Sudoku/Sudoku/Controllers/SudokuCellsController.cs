using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using Sudoku.Application.Ml;
using Sudoku.Application.ModelsActive;
using Sudoku.Application.Sudoku;
using Sudoku.Contracts;

namespace Sudoku.Controllers;

[ApiController]
[Route("api/sudoku/cells")]
public sealed class SudokuCellsController : ControllerBase
{
    private readonly ISender _sender;
    private readonly ILogger<SudokuCellsController> _logger;

    public SudokuCellsController(
        ISender sender,
        ILogger<SudokuCellsController> logger)
    {
        _sender = sender;
        _logger = logger;
    }

    [HttpPut("inference")]
    [ProducesResponseType(typeof(DigitInferenceApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status409Conflict)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status422UnprocessableEntity)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status502BadGateway)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status503ServiceUnavailable)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status504GatewayTimeout)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> InferAsync(
        [FromBody] DigitInferenceApiEntry entry,
        CancellationToken cancellationToken)
    {
        var command = new InferSudokuCellDigitCommand(
            entry.Image.MimeType,
            entry.Image.Base64,
            entry.CenterAreaRatio,
            entry.MinComponentAreaRatio,
            entry.LineArtifactMinSpanRatio,
            entry.LineArtifactMaxThicknessRatio
        );

        _logger.LogInformation("Rozpoczęto inferencję pojedynczej komórki sudoku.");

        try
        {
            var result = await _sender.Send(command, cancellationToken);
            _logger.LogInformation("Zakończono inferencję pojedynczej komórki sudoku. Digit={Digit}.", result.Digit);
            return Ok(new DigitInferenceApiResponse(result.Digit));
        }
        catch (ValidationException exception)
        {
            return MapValidationError(exception);
        }
        catch (ActiveModelNotConfiguredException exception)
        {
            _logger.LogWarning(
                exception,
                "Brak aktywnego modelu inferencyjnego. ErrorType={ErrorType}.",
                InferSudokuCellDigitErrorTypes.ActiveModelNotConfigured);

            return Conflict(new ErrorApiResponse(
                ErrorType: InferSudokuCellDigitErrorTypes.ActiveModelNotConfigured,
                Message: exception.Message));
        }
        catch (ActiveModelPointerInvalidException exception)
        {
            _logger.LogWarning(
                exception,
                "Wskaźnik aktywnego modelu inferencyjnego jest niespójny. ErrorType={ErrorType}. ModelName={ModelName}.",
                InferSudokuCellDigitErrorTypes.ActiveModelPointerInvalid,
                exception.ModelName);

            return Conflict(new ErrorApiResponse(
                ErrorType: InferSudokuCellDigitErrorTypes.ActiveModelPointerInvalid,
                Message: exception.Message));
        }
        catch (ActiveModelNotFoundException exception)
        {
            _logger.LogWarning(
                exception,
                "Aktywny model inferencyjny nie istnieje w rejestrze. ErrorType={ErrorType}. ModelName={ModelName}.",
                InferSudokuCellDigitErrorTypes.ActiveModelPointerInvalid,
                exception.ModelName);

            return Conflict(new ErrorApiResponse(
                ErrorType: InferSudokuCellDigitErrorTypes.ActiveModelPointerInvalid,
                Message: exception.Message));
        }
        catch (ActiveModelCannotUseForInferenceException exception)
        {
            _logger.LogWarning(
                exception,
                "Aktywny model nie może zostać użyty do inferencji. ErrorType={ErrorType}. ModelName={ModelName}.",
                InferSudokuCellDigitErrorTypes.ActiveModelCannotUseForInference,
                exception.ModelName);

            return Conflict(new ErrorApiResponse(
                ErrorType: InferSudokuCellDigitErrorTypes.ActiveModelCannotUseForInference,
                Message: exception.Message));
        }
        catch (ActiveModelManifestInvalidException exception)
        {
            _logger.LogWarning(
                exception,
                "Manifest aktywnego modelu inferencyjnego jest niepoprawny. ErrorType={ErrorType}. ModelName={ModelName}.",
                InferSudokuCellDigitErrorTypes.ActiveModelManifestInvalid,
                exception.ModelName);

            return Conflict(new ErrorApiResponse(
                ErrorType: InferSudokuCellDigitErrorTypes.ActiveModelManifestInvalid,
                Message: exception.Message));
        }
        catch (MlOperationFailedException exception) when (
            string.Equals(
                exception.ErrorType,
                InferSudokuCellDigitErrorTypes.CellImageNotProcessable,
                StringComparison.Ordinal))
        {
            _logger.LogWarning(
                exception,
                "Serwis ML odrzucił obraz komórki jako nieprzetwarzalny. ErrorType={ErrorType}.",
                exception.ErrorType);

            return UnprocessableEntity(new ErrorApiResponse(
                ErrorType: exception.ErrorType,
                Message: exception.Message));
        }
        catch (MlOperationFailedException exception)
        {
            _logger.LogError(
                exception,
                "Serwis ML zwrócił niepoprawną odpowiedź dla inferencji komórki. ErrorType={ErrorType}.",
                exception.ErrorType);

            return StatusCode(
                StatusCodes.Status502BadGateway,
                new ErrorApiResponse(
                    ErrorType: string.IsNullOrWhiteSpace(exception.ErrorType)
                        ? InferSudokuCellDigitErrorTypes.MlInvalidResponse
                        : exception.ErrorType,
                    Message: exception.Message));
        }
        catch (MlServiceUnavailableException exception)
        {
            _logger.LogError(
                exception,
                "Serwis ML jest niedostępny podczas inferencji komórki. ErrorType={ErrorType}.",
                InferSudokuCellDigitErrorTypes.MlUnavailable);

            return StatusCode(
                StatusCodes.Status503ServiceUnavailable,
                new ErrorApiResponse(
                    ErrorType: InferSudokuCellDigitErrorTypes.MlUnavailable,
                    Message: exception.Message));
        }
        catch (MlServiceTimeoutException exception)
        {
            _logger.LogError(
                exception,
                "Serwis ML przekroczył limit czasu podczas inferencji komórki. ErrorType={ErrorType}.",
                InferSudokuCellDigitErrorTypes.MlTimeout);

            return StatusCode(
                StatusCodes.Status504GatewayTimeout,
                new ErrorApiResponse(
                    ErrorType: InferSudokuCellDigitErrorTypes.MlTimeout,
                    Message: exception.Message));
        }
        catch (ActiveModelPointerReadException exception)
        {
            _logger.LogError(
                exception,
                "Nie udało się odczytać wskaźnika aktywnego modelu inferencyjnego.");

            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: InferSudokuCellDigitErrorTypes.ActiveModelPointerInvalid,
                    Message: "Nie udało się odczytać wskaźnika aktywnego modelu inferencyjnego."));
        }
    }

    private static IActionResult MapValidationError(ValidationException exception)
    {
        var failure = exception.Errors.FirstOrDefault();
        var errorType = failure?.ErrorCode ?? InferSudokuCellDigitErrorTypes.InvalidRequest;
        var message = failure?.ErrorMessage ?? "Nieprawidłowe dane wejściowe.";

        return new BadRequestObjectResult(new ErrorApiResponse(
            ErrorType: errorType,
            Message: message));
    }
}
