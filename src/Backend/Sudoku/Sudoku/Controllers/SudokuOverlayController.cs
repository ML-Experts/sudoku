using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using Sudoku.Application.Ml;
using Sudoku.Application.SudokuOverlay;
using Sudoku.Contracts;

namespace Sudoku.Controllers;

[ApiController]
[Route("api/sudoku/overlay")]
public sealed class SudokuOverlayController : ControllerBase
{
    private readonly ISender _sender;
    private readonly ILogger<SudokuOverlayController> _logger;

    public SudokuOverlayController(
        ISender sender,
        ILogger<SudokuOverlayController> logger)
    {
        _sender = sender;
        _logger = logger;
    }

    [HttpPost("cells")]
    [ProducesResponseType(typeof(ImageApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status422UnprocessableEntity)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status502BadGateway)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status503ServiceUnavailable)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status504GatewayTimeout)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> RenderCellAsync(
        [FromBody] RenderSudokuOverlayCellApiEntry entry,
        CancellationToken cancellationToken)
    {
        var command = new RenderSudokuOverlayCellCommand(
            CellImageMimeType: entry.CellImage?.MimeType,
            CellImageBase64: entry.CellImage?.Base64,
            Digit: entry.Digit,
            RowIndex: entry.RowIndex,
            ColumnIndex: entry.ColumnIndex);

        _logger.LogInformation(
            "Rozpoczęto renderowanie overlay komórki sudoku. Digit={Digit}. RowIndex={RowIndex}. ColumnIndex={ColumnIndex}.",
            entry.Digit,
            entry.RowIndex,
            entry.ColumnIndex);

        try
        {
            var result = await _sender.Send(command, cancellationToken);

            _logger.LogInformation(
                "Zakończono renderowanie overlay komórki sudoku. Digit={Digit}. RowIndex={RowIndex}. ColumnIndex={ColumnIndex}.",
                entry.Digit,
                entry.RowIndex,
                entry.ColumnIndex);

            return Ok(new ImageApiResponse(
                MimeType: result.MimeType,
                Base64: result.Base64));
        }
        catch (ValidationException exception)
        {
            return MapValidationError(exception);
        }
        catch (MlOperationFailedException exception) when (
            string.Equals(
                exception.ErrorType,
                RenderSudokuOverlayCellErrorTypes.CellImageNotProcessable,
                StringComparison.Ordinal)
            || string.Equals(
                exception.ErrorType,
                RenderSudokuOverlayCellErrorTypes.OverlayRenderNotPossible,
                StringComparison.Ordinal))
        {
            _logger.LogWarning(
                exception,
                "Serwis ML odrzucił renderowanie overlay komórki sudoku. ErrorType={ErrorType}. Digit={Digit}. RowIndex={RowIndex}. ColumnIndex={ColumnIndex}.",
                exception.ErrorType,
                entry.Digit,
                entry.RowIndex,
                entry.ColumnIndex);

            return UnprocessableEntity(new ErrorApiResponse(
                ErrorType: exception.ErrorType,
                Message: exception.Message));
        }
        catch (MlOperationFailedException exception)
        {
            _logger.LogError(
                exception,
                "Serwis ML zwrócił niepoprawną odpowiedź dla renderowania overlay komórki sudoku. Digit={Digit}. RowIndex={RowIndex}. ColumnIndex={ColumnIndex}.",
                entry.Digit,
                entry.RowIndex,
                entry.ColumnIndex);

            return StatusCode(
                StatusCodes.Status502BadGateway,
                new ErrorApiResponse(
                    ErrorType: RenderSudokuOverlayCellErrorTypes.MlInvalidResponse,
                    Message: exception.Message));
        }
        catch (MlServiceUnavailableException exception)
        {
            _logger.LogError(
                exception,
                "Serwis ML jest niedostępny podczas renderowania overlay komórki sudoku. Digit={Digit}. RowIndex={RowIndex}. ColumnIndex={ColumnIndex}.",
                entry.Digit,
                entry.RowIndex,
                entry.ColumnIndex);

            return StatusCode(
                StatusCodes.Status503ServiceUnavailable,
                new ErrorApiResponse(
                    ErrorType: RenderSudokuOverlayCellErrorTypes.MlUnavailable,
                    Message: exception.Message));
        }
        catch (MlServiceTimeoutException exception)
        {
            _logger.LogError(
                exception,
                "Serwis ML przekroczył limit czasu podczas renderowania overlay komórki sudoku. Digit={Digit}. RowIndex={RowIndex}. ColumnIndex={ColumnIndex}.",
                entry.Digit,
                entry.RowIndex,
                entry.ColumnIndex);

            return StatusCode(
                StatusCodes.Status504GatewayTimeout,
                new ErrorApiResponse(
                    ErrorType: RenderSudokuOverlayCellErrorTypes.MlTimeout,
                    Message: exception.Message));
        }
        catch (Exception exception)
        {
            _logger.LogError(
                exception,
                "Wystąpił nieobsłużony błąd podczas renderowania overlay komórki sudoku. Digit={Digit}. RowIndex={RowIndex}. ColumnIndex={ColumnIndex}.",
                entry.Digit,
                entry.RowIndex,
                entry.ColumnIndex);

            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: RenderSudokuOverlayCellErrorTypes.InternalServerError,
                    Message: "Wystąpił nieoczekiwany błąd podczas renderowania overlay komórki sudoku."));
        }
    }

    private static IActionResult MapValidationError(ValidationException exception)
    {
        var failure = exception.Errors.FirstOrDefault();
        var errorType = failure?.ErrorCode ?? RenderSudokuOverlayCellErrorTypes.InvalidRequest;
        var message = failure?.ErrorMessage ?? "Nieprawidłowe dane wejściowe.";

        return new BadRequestObjectResult(new ErrorApiResponse(
            ErrorType: errorType,
            Message: message));
    }
}
