using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using System.Text.Json;
using Sudoku.Application.Storage;
using Sudoku.Application.SudokuSolve;
using Sudoku.Contracts;

namespace Sudoku.Controllers;

[ApiController]
[Route("api/sudoku")]
public sealed class SudokuSolveController : ControllerBase
{
    private readonly ISender _sender;
    private readonly ILogger<SudokuSolveController> _logger;

    public SudokuSolveController(
        ISender sender,
        ILogger<SudokuSolveController> logger)
    {
        _sender = sender;
        _logger = logger;
    }

    [HttpPost("solve")]
    [ProducesResponseType(typeof(SolveSessionApiResponse), StatusCodes.Status202Accepted)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status409Conflict)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status422UnprocessableEntity)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> SolveAsync(
        [FromBody] SolveSudokuApiEntry? entry,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation("Rozpoczęto próbę uruchomienia sesji solve sudoku.");

        try
        {
            var result = await _sender.Send(new StartSudokuSolveCommand(entry?.Grid), cancellationToken);

            _logger.LogInformation(
                "Uruchomiono sesję solve sudoku. SolveSessionId={SolveSessionId}, Status={Status}.",
                result.SolveSessionId,
                result.Status);

            return StatusCode(
                StatusCodes.Status202Accepted,
                new SolveSessionApiResponse(
                    SolveSessionId: result.SolveSessionId,
                    Status: result.Status,
                    ProgressChannelUrl: result.ProgressChannelUrl));
        }
        catch (ValidationException exception)
        {
            return MapValidationError(exception);
        }
        catch (ActiveSolveSessionAlreadyExistsException exception)
        {
            _logger.LogWarning(
                exception,
                "Odrzucono start nowej sesji solve z powodu aktywnej sesji. ActiveSolveSessionId={SolveSessionId}.",
                exception.ActiveSolveSessionId);

            return Conflict(new ErrorApiResponse(
                ErrorType: SolveSudokuErrorTypes.SolveSessionAlreadyActive,
                Message: exception.Message));
        }
        catch (SudokuGridConflictsException exception)
        {
            _logger.LogWarning(
                exception,
                "Odrzucono grid solve z powodu konfliktu reguł sudoku. ErrorType={ErrorType}.",
                SolveSudokuErrorTypes.GridConflictsWithSudokuRules);

            return UnprocessableEntity(new ErrorApiResponse(
                ErrorType: SolveSudokuErrorTypes.GridConflictsWithSudokuRules,
                Message: exception.Message));
        }
        catch (SolveSessionStartException exception)
        {
            _logger.LogError(
                exception,
                "Nie udało się uruchomić sesji solve sudoku. ErrorType={ErrorType}.",
                exception.ErrorType);

            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: exception.ErrorType,
                    Message: exception.Message));
        }
        catch (InvalidOperationException exception)
        {
            _logger.LogError(
                exception,
                "Wykryto niespójny stan podczas uruchamiania sesji solve sudoku. ErrorType={ErrorType}.",
                SolveSudokuErrorTypes.SolveSessionInvariantViolation);

            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: SolveSudokuErrorTypes.SolveSessionInvariantViolation,
                    Message: "Backend wykrył niespójny stan sesji rozwiązywania sudoku."));
        }
    }

    [HttpGet("solve/active")]
    [ProducesResponseType(typeof(SolveSessionApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> GetActiveAsync(CancellationToken cancellationToken)
    {
        _logger.LogInformation("Rozpoczęto odczyt aktywnej sesji solve sudoku.");

        try
        {
            var result = await _sender.Send(new GetActiveSolveSessionQuery(), cancellationToken);
            if (!result.HasActiveSession || result.Session is null)
            {
                _logger.LogDebug("Brak aktywnej sesji solve sudoku.");
                return NoContent();
            }

            _logger.LogInformation(
                "Znaleziono aktywną sesję solve sudoku. SolveSessionId={SolveSessionId}, Status={Status}.",
                result.Session.SolveSessionId,
                result.Session.Status);

            return Ok(new SolveSessionApiResponse(
                SolveSessionId: result.Session.SolveSessionId,
                Status: result.Session.Status,
                ProgressChannelUrl: result.Session.ProgressChannelUrl));
        }
        catch (InvalidOperationException exception)
        {
            _logger.LogError(
                exception,
                "Wykryto niespójny stan aktywnej sesji solve sudoku. ErrorType={ErrorType}.",
                GetActiveSolveSessionErrorTypes.InvariantViolation);

            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: GetActiveSolveSessionErrorTypes.InvariantViolation,
                    Message: "Wykryto niespójny stan aktywnej sesji rozwiązywania sudoku."));
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidDataException
                                         or JsonException
                                         or FileStorageItemNotFoundException)
        {
            _logger.LogError(
                exception,
                "Nie udało się odczytać aktywnej sesji solve sudoku. ErrorType={ErrorType}.",
                GetActiveSolveSessionErrorTypes.ReadFailed);

            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: GetActiveSolveSessionErrorTypes.ReadFailed,
                    Message: "Nie udało się odczytać aktywnej sesji rozwiązywania sudoku."));
        }
    }

    private static IActionResult MapValidationError(ValidationException exception)
    {
        var failure = exception.Errors.FirstOrDefault();
        var errorType = failure?.ErrorCode ?? SolveSudokuErrorTypes.InvalidRequest;
        var message = failure?.ErrorMessage ?? "Nieprawidłowe dane wejściowe.";

        return new ObjectResult(new ErrorApiResponse(
            ErrorType: errorType,
            Message: message))
        {
            StatusCode = StatusCodes.Status400BadRequest
        };
    }
}
