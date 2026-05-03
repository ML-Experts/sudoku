using System.Text.Json;
using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using Sudoku.Application.Trainings;
using Sudoku.Contracts;

namespace Sudoku.Controllers;

[ApiController]
[Route("internal/ml/trainings")]
public sealed class InternalMlTrainingsController : ControllerBase
{
    private static readonly TimeSpan EventProcessingTimeout = TimeSpan.FromSeconds(60);

    private readonly ISender _sender;

    public InternalMlTrainingsController(ISender sender)
    {
        _sender = sender;
    }

    [HttpPost("{runName}/events")]
    [ProducesResponseType(typeof(TrainingRunEventAckApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status404NotFound)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status409Conflict)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status422UnprocessableEntity)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status504GatewayTimeout)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> RecordEventAsync(
        [FromRoute] string runName,
        [FromBody] TrainingRunEventApiEntry? entry)
    {
        var command = new RecordTrainingRunEventCommand(
            RunName: runName,
            Sequence: entry?.Sequence ?? 0,
            EventType: entry?.EventType,
            Status: entry?.Status,
            Stage: entry?.Stage,
            OccurredAtUtc: entry?.OccurredAtUtc ?? default,
            Message: entry?.Message,
            Progress: ToProgressDto(entry?.Progress),
            Result: ToResultDto(entry?.Result),
            Failure: ToFailureDto(entry?.Failure),
            Warnings: entry?.Warnings);

        try
        {
            using var timeout = new CancellationTokenSource(EventProcessingTimeout);
            var result = await _sender.Send(command, timeout.Token);
            return Ok(new TrainingRunEventAckApiResponse(
                Accepted: result.Accepted,
                RunName: result.RunName,
                Status: result.Status,
                LastAcceptedSequence: result.LastAcceptedSequence,
                Disposition: result.Disposition));
        }
        catch (OperationCanceledException)
        {
            return StatusCode(
                StatusCodes.Status504GatewayTimeout,
                new ErrorApiResponse(
                    ErrorType: RecordTrainingRunEventErrorTypes.TrainingRunEventPersistFailed,
                    Message: "Przekroczono limit czasu obsługi eventu treningowego."));
        }
        catch (ValidationException exception)
        {
            return MapValidationError(exception);
        }
        catch (TrainingRunNotFoundException exception)
        {
            return NotFound(new ErrorApiResponse(
                ErrorType: RecordTrainingRunEventErrorTypes.TrainingRunNotFound,
                Message: exception.Message));
        }
        catch (TrainingRunEventArtifactNotReadyException exception)
        {
            return Conflict(new ErrorApiResponse(
                ErrorType: RecordTrainingRunEventErrorTypes.TrainingRunArtifactNotReady,
                Message: exception.Message));
        }
        catch (TrainingRunEventConflictException exception)
        {
            return Conflict(new ErrorApiResponse(
                ErrorType: RecordTrainingRunEventErrorTypes.TrainingRunEventConflict,
                Message: exception.Message));
        }
        catch (TrainingRunEventInvalidTransitionException exception)
        {
            return UnprocessableEntity(new ErrorApiResponse(
                ErrorType: RecordTrainingRunEventErrorTypes.TrainingRunEventInvalidTransition,
                Message: exception.Message));
        }
        catch (TrainingRunEventPersistenceException exception)
        {
            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: RecordTrainingRunEventErrorTypes.TrainingRunEventPersistFailed,
                    Message: exception.Message));
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidOperationException
                                         or InvalidDataException
                                         or JsonException)
        {
            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: RecordTrainingRunEventErrorTypes.TrainingRunEventPersistFailed,
                    Message: "Nie udało się obsłużyć eventu treningowego."));
        }
    }

    private static TrainingRunProgressDto? ToProgressDto(TrainingRunProgressApiEntry? entry)
    {
        return entry is null
            ? null
            : new TrainingRunProgressDto(
                Percent: entry.Percent,
                Epoch: entry.EpochCurrent,
                TotalEpochs: entry.EpochTotal,
                TrainLoss: entry.TrainLoss,
                ValidationLoss: entry.ValidationLoss,
                TrainAccuracy: entry.TrainAccuracy,
                ValidationAccuracy: entry.ValidationAccuracy,
                EtaSeconds: entry.EtaSeconds);
    }

    private static TrainingRunEventResultDto? ToResultDto(TrainingRunEventResultApiEntry? entry)
    {
        return entry is null
            ? null
            : new TrainingRunEventResultDto(
                ProducedModelName: entry.ProducedModelName,
                PrimaryArtifactRelativePath: entry.PrimaryArtifactRelativePath,
                ReportStatus: entry.ReportStatus,
                ReportRelativePath: entry.ReportRelativePath,
                SummaryRelativePath: entry.SummaryRelativePath,
                MetricsRelativePath: entry.MetricsRelativePath,
                ConfusionMatrixRelativePath: entry.ConfusionMatrixRelativePath,
                CanUseProducedModelForInference: entry.CanUseProducedModelForInference,
                MetricsSummary: ToMetricsSummaryDto(entry.MetricsSummary));
    }

    private static TrainingMetricsSummaryDto? ToMetricsSummaryDto(TrainingMetricsSummaryApiEntry? entry)
    {
        return entry is null
            ? null
            : new TrainingMetricsSummaryDto(
                Accuracy: entry.Accuracy,
                MacroF1: entry.MacroF1);
    }

    private static TrainingRunFailureDto? ToFailureDto(TrainingRunFailureApiEntry? entry)
    {
        return entry is null
            ? null
            : new TrainingRunFailureDto(
                ErrorType: entry.ErrorType,
                Message: entry.Message,
                CanUseProducedModelForInference: entry.CanUseProducedModelForInference);
    }

    private static IActionResult MapValidationError(ValidationException exception)
    {
        var failure = exception.Errors.FirstOrDefault();
        var message = failure?.ErrorMessage ?? "Nieprawidłowe dane wejściowe.";

        return new ObjectResult(new ErrorApiResponse(
            ErrorType: RecordTrainingRunEventErrorTypes.InvalidRequest,
            Message: message))
        {
            StatusCode = StatusCodes.Status400BadRequest
        };
    }
}
