using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Text.Json;
using FluentValidation;
using Sudoku.Application.Ml;
using Sudoku.Application.Storage;
using Sudoku.Application.Trainings;
using Sudoku.Contracts;

namespace Sudoku.Controllers;

[ApiController]
[Route("api/trainings")]
public sealed class TrainingsController : ControllerBase
{
    private readonly ISender _sender;

    public TrainingsController(ISender sender)
    {
        _sender = sender;
    }

    [Authorize]
    [HttpPost]
    [ProducesResponseType(typeof(TrainingRunApiResponse), StatusCodes.Status202Accepted)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status404NotFound)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status409Conflict)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status422UnprocessableEntity)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status502BadGateway)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status503ServiceUnavailable)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status504GatewayTimeout)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> CreateAsync(
        [FromBody] CreateTrainingRunApiEntry? entry,
        CancellationToken cancellationToken)
    {
        var command = new CreateTrainingRunCommand(
            BaseModelName: entry?.BaseModelName,
            ProcessedDatasetName: entry?.ProcessedDatasetName);

        try
        {
            var result = await _sender.Send(command, cancellationToken);
            return StatusCode(StatusCodes.Status202Accepted, ToTrainingRunApiResponse(result));
        }
        catch (ValidationException exception)
        {
            return MapValidationError(exception);
        }
        catch (ActiveTrainingRunAlreadyExistsException exception)
        {
            return Conflict(new ErrorApiResponse(
                ErrorType: CreateTrainingRunErrorTypes.TrainingRunAlreadyActive,
                Message: exception.Message));
        }
        catch (BaseModelNotFoundException exception)
        {
            return NotFound(new ErrorApiResponse(
                ErrorType: CreateTrainingRunErrorTypes.BaseModelNotFound,
                Message: exception.Message));
        }
        catch (ProcessedDatasetNotFoundException exception)
        {
            return NotFound(new ErrorApiResponse(
                ErrorType: CreateTrainingRunErrorTypes.ProcessedDatasetNotFound,
                Message: exception.Message));
        }
        catch (BaseModelCannotStartTrainingException exception)
        {
            return UnprocessableEntity(new ErrorApiResponse(
                ErrorType: CreateTrainingRunErrorTypes.BaseModelCannotStartTraining,
                Message: exception.Message));
        }
        catch (ProcessedDatasetCannotStartTrainingException exception)
        {
            return UnprocessableEntity(new ErrorApiResponse(
                ErrorType: CreateTrainingRunErrorTypes.ProcessedDatasetCannotStartTraining,
                Message: exception.Message));
        }
        catch (TrainingProfileMismatchException exception)
        {
            return BadRequest(new ErrorApiResponse(
                ErrorType: CreateTrainingRunErrorTypes.TrainingProfileMismatch,
                Message: exception.Message));
        }
        catch (MlOperationFailedException exception)
        {
            return StatusCode(
                StatusCodes.Status502BadGateway,
                new ErrorApiResponse(
                    ErrorType: string.IsNullOrWhiteSpace(exception.ErrorType)
                        ? CreateTrainingRunErrorTypes.MlTrainingStartRejected
                        : exception.ErrorType,
                    Message: exception.Message));
        }
        catch (MlServiceUnavailableException exception)
        {
            return StatusCode(
                StatusCodes.Status503ServiceUnavailable,
                new ErrorApiResponse(
                    ErrorType: CreateTrainingRunErrorTypes.MlTrainingStartUnavailable,
                    Message: exception.Message));
        }
        catch (MlServiceTimeoutException exception)
        {
            return StatusCode(
                StatusCodes.Status504GatewayTimeout,
                new ErrorApiResponse(
                    ErrorType: CreateTrainingRunErrorTypes.MlTrainingStartTimeout,
                    Message: exception.Message));
        }
        catch (Exception exception) when (exception is TrainingRunReservationException
                                         or TrainingRunStartFailedException
                                         or InvalidOperationException
                                         or IOException
                                         or UnauthorizedAccessException
                                         or InvalidDataException
                                         or JsonException
                                         or FileStorageConflictException
                                         or FileStorageItemNotFoundException)
        {
            var errorType = exception is InvalidOperationException
                ? CreateTrainingRunErrorTypes.TrainingRunInvariantViolation
                : CreateTrainingRunErrorTypes.TrainingRunStartFailed;

            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: errorType,
                    Message: "Nie udało się uruchomić runu treningowego."));
        }
    }

    [Authorize]
    [HttpGet("active")]
    [ProducesResponseType(typeof(TrainingRunApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> GetActiveAsync(CancellationToken cancellationToken)
    {
        try
        {
            var result = await _sender.Send(new GetActiveTrainingRunQuery(), cancellationToken);
            if (!result.HasActiveRun || result.Run is null)
            {
                return NoContent();
            }

            return Ok(new TrainingRunApiResponse(
                RunName: result.Run.RunName,
                Status: result.Run.Status,
                CreatedAtUtc: result.Run.CreatedAtUtc,
                BaseModelName: result.Run.BaseModelName,
                ProducedModelName: result.Run.ProducedModelName,
                ProcessedDatasetName: result.Run.ProcessedDatasetName,
                TrainingMode: result.Run.TrainingMode,
                TrainingProfileName: result.Run.TrainingProfileName,
                AugmentationProfileName: result.Run.AugmentationProfileName,
                BenchmarkName: result.Run.BenchmarkName,
                Seed: result.Run.Seed,
                ProgressChannelUrl: result.Run.ProgressChannelUrl));
        }
        catch (InvalidOperationException)
        {
            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: GetActiveTrainingRunErrorTypes.InvariantViolation,
                    Message: "Wykryto niespójny stan aktywnych runów treningowych."));
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidDataException
                                         or JsonException
                                         or FileStorageItemNotFoundException)
        {
            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: GetActiveTrainingRunErrorTypes.ReadFailed,
                    Message: "Nie udało się odczytać aktywnego runu treningowego."));
        }
    }

    private static TrainingRunApiResponse ToTrainingRunApiResponse(CreateTrainingRunCommandResultDto result)
    {
        return new TrainingRunApiResponse(
            RunName: result.RunName,
            Status: result.Status,
            CreatedAtUtc: result.CreatedAtUtc,
            BaseModelName: result.BaseModelName,
            ProducedModelName: result.ProducedModelName,
            ProcessedDatasetName: result.ProcessedDatasetName,
            TrainingMode: result.TrainingMode,
            TrainingProfileName: result.TrainingProfileName,
            AugmentationProfileName: result.AugmentationProfileName,
            BenchmarkName: result.BenchmarkName,
            Seed: result.Seed,
            ProgressChannelUrl: result.ProgressChannelUrl);
    }

    private static IActionResult MapValidationError(ValidationException exception)
    {
        var failure = exception.Errors.FirstOrDefault();
        var errorType = failure?.ErrorCode ?? CreateTrainingRunErrorTypes.InvalidRequest;
        var message = failure?.ErrorMessage ?? "Nieprawidłowe dane wejściowe.";

        return new ObjectResult(new ErrorApiResponse(
            ErrorType: errorType,
            Message: message))
        {
            StatusCode = StatusCodes.Status400BadRequest
        };
    }
}
