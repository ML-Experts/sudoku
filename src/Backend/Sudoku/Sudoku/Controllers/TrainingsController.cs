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
    private readonly ILogger<TrainingsController> _logger;

    public TrainingsController(
        ISender sender,
        ILogger<TrainingsController> logger)
    {
        _sender = sender;
        _logger = logger;
    }

    [Authorize]
    [HttpGet]
    [ProducesResponseType(typeof(TrainingRunsListApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> ListAsync(CancellationToken cancellationToken)
    {
        _logger.LogInformation("Rozpoczęto listowanie runów treningowych.");

        try
        {
            var result = await _sender.Send(new ListTrainingRunsQuery(), cancellationToken);
            var items = result.Items
                .Select(ToTrainingRunListItemApiResponse)
                .ToArray();

            _logger.LogInformation(
                "Zakończono listowanie runów treningowych. TotalCount={TotalCount}.",
                result.TotalCount);

            return Ok(new TrainingRunsListApiResponse(
                Items: items,
                TotalCount: result.TotalCount));
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidDataException
                                         or JsonException
                                         or FileStorageItemNotFoundException)
        {
            _logger.LogError(
                exception,
                "Nie udało się odczytać listy runów treningowych. ErrorType={ErrorType}.",
                ListTrainingRunsErrorTypes.ReadFailed);

            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: ListTrainingRunsErrorTypes.ReadFailed,
                    Message: "Nie udało się odczytać listy runów treningowych."));
        }
    }

    [Authorize]
    [HttpGet("{runName}")]
    [ProducesResponseType(typeof(TrainingRunDetailsApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status404NotFound)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status409Conflict)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status422UnprocessableEntity)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> GetByRunNameAsync(
        [FromRoute] string? runName,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation(
            "Rozpoczęto odczyt szczegółów runu treningowego. RunName={RunName}.",
            runName);

        try
        {
            var result = await _sender.Send(new GetTrainingRunDetailsQuery(runName), cancellationToken);
            var response = ToTrainingRunDetailsApiResponse(result.Details);

            _logger.LogInformation(
                "Zakończono odczyt szczegółów runu treningowego. RunName={RunName}, Status={Status}, ReportStatus={ReportStatus}.",
                response.RunName,
                response.Status,
                response.Report.Status);

            return Ok(response);
        }
        catch (ValidationException exception)
        {
            return MapValidationError(exception, GetTrainingRunDetailsErrorTypes.InvalidTrainingRunName);
        }
        catch (TrainingRunDetailsNotFoundException exception)
        {
            _logger.LogWarning(
                exception,
                "Nie znaleziono runu treningowego. RunName={RunName}, ErrorType={ErrorType}.",
                runName,
                GetTrainingRunDetailsErrorTypes.TrainingRunNotFound);

            return NotFound(new ErrorApiResponse(
                ErrorType: GetTrainingRunDetailsErrorTypes.TrainingRunNotFound,
                Message: exception.Message));
        }
        catch (TrainingRunDetailsConflictException exception)
        {
            _logger.LogWarning(
                exception,
                "Wykryto niespójne szczegóły runu treningowego. RunName={RunName}, ErrorType={ErrorType}.",
                runName,
                GetTrainingRunDetailsErrorTypes.TrainingRunDetailsConflict);

            return Conflict(new ErrorApiResponse(
                ErrorType: GetTrainingRunDetailsErrorTypes.TrainingRunDetailsConflict,
                Message: exception.Message));
        }
        catch (TrainingRunReportInvalidException exception)
        {
            _logger.LogError(
                exception,
                "Raport runu treningowego nie spełnia kontraktu. RunName={RunName}, ErrorType={ErrorType}.",
                runName,
                GetTrainingRunDetailsErrorTypes.TrainingRunReportInvalid);

            return UnprocessableEntity(new ErrorApiResponse(
                ErrorType: GetTrainingRunDetailsErrorTypes.TrainingRunReportInvalid,
                Message: exception.Message));
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidDataException
                                         or JsonException
                                         or FileStorageItemNotFoundException
                                         or InvalidOperationException)
        {
            _logger.LogError(
                exception,
                "Nie udało się odczytać szczegółów runu treningowego. RunName={RunName}, ErrorType={ErrorType}.",
                runName,
                GetTrainingRunDetailsErrorTypes.TrainingRunDetailsReadFailed);

            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: GetTrainingRunDetailsErrorTypes.TrainingRunDetailsReadFailed,
                    Message: "Nie udało się odczytać szczegółów runu treningowego."));
        }
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
            ProcessedDatasetName: entry?.ProcessedDatasetName,
            TrainingParameters: entry?.TrainingParameters is null
                ? null
                : new TrainingRunRequestedParametersDto(
                    Epochs: entry.TrainingParameters.Epochs,
                    LearningRate: entry.TrainingParameters.LearningRate,
                    BatchSize: entry.TrainingParameters.BatchSize,
                    EarlyStoppingPatience: entry.TrainingParameters.EarlyStoppingPatience,
                    LrSchedulerPatience: entry.TrainingParameters.LrSchedulerPatience,
                    LrSchedulerFactor: entry.TrainingParameters.LrSchedulerFactor,
                    FineTuningPolicy: entry.TrainingParameters.FineTuningPolicy,
                    UseBestCheckpoint: entry.TrainingParameters.UseBestCheckpoint));

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
    [HttpPost("{runName}/cancel")]
    [ProducesResponseType(typeof(CancelTrainingRunApiResponse), StatusCodes.Status202Accepted)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status502BadGateway)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status503ServiceUnavailable)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status504GatewayTimeout)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> CancelAsync(
        [FromRoute] string? runName,
        CancellationToken cancellationToken)
    {
        try
        {
            var result = await _sender.Send(new CancelTrainingRunCommand(runName), cancellationToken);
            return StatusCode(StatusCodes.Status202Accepted, new CancelTrainingRunApiResponse(
                RunName: result.RunName,
                Status: result.Status,
                RequestDisposition: result.RequestDisposition,
                Message: result.Message,
                ProgressChannelUrl: result.ProgressChannelUrl));
        }
        catch (ValidationException exception)
        {
            return MapValidationError(exception, CancelTrainingRunErrorTypes.InvalidTrainingRunName);
        }
        catch (MlOperationFailedException exception)
        {
            return StatusCode(
                StatusCodes.Status502BadGateway,
                new ErrorApiResponse(
                    ErrorType: string.IsNullOrWhiteSpace(exception.ErrorType)
                        ? CancelTrainingRunErrorTypes.MlRejected
                        : exception.ErrorType,
                    Message: exception.Message));
        }
        catch (MlServiceUnavailableException exception)
        {
            return StatusCode(
                StatusCodes.Status503ServiceUnavailable,
                new ErrorApiResponse(
                    ErrorType: CancelTrainingRunErrorTypes.MlUnavailable,
                    Message: exception.Message));
        }
        catch (MlServiceTimeoutException exception)
        {
            return StatusCode(
                StatusCodes.Status504GatewayTimeout,
                new ErrorApiResponse(
                    ErrorType: CancelTrainingRunErrorTypes.MlTimeout,
                    Message: exception.Message));
        }
        catch (TrainingRunCancelPersistenceException)
        {
            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: CancelTrainingRunErrorTypes.PersistenceFailed,
                    Message: "Nie udało się zapisać metadanych anulowania runu treningowego."));
        }
        catch (Exception exception) when (exception is InvalidOperationException
                                         or IOException
                                         or UnauthorizedAccessException
                                         or InvalidDataException
                                         or JsonException
                                         or FileStorageItemNotFoundException)
        {
            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: CancelTrainingRunErrorTypes.InvariantViolation,
                    Message: "Nie udało się anulować runu treningowego z powodu niespójnego stanu backendu."));
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
                EffectiveParameters: result.Run.EffectiveParameters is null
                    ? null
                    : ToTrainingRunEffectiveParametersApiResponse(result.Run.EffectiveParameters),
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

    private static TrainingRunDetailsApiResponse ToTrainingRunDetailsApiResponse(TrainingRunDetailsDto details)
    {
        return new TrainingRunDetailsApiResponse(
            RunName: details.RunName,
            Status: details.Status,
            Stage: details.Stage,
            CreatedAtUtc: details.CreatedAtUtc,
            StartedAtUtc: details.StartedAtUtc,
            FinishedAtUtc: details.FinishedAtUtc,
            BaseModel: ToTrainingRunModelReferenceApiResponse(details.BaseModel),
            ProducedModel: details.ProducedModel is null
                ? null
                : ToTrainingRunModelReferenceApiResponse(details.ProducedModel),
            Dataset: new TrainingRunDatasetDetailsApiResponse(
                ProcessedDatasetName: details.Dataset.ProcessedDatasetName,
                PreprocessingProfile: details.Dataset.PreprocessingProfile,
                SampleCounts: details.Dataset.SampleCounts is null
                    ? null
                    : new TrainingDatasetSampleCountsApiResponse(
                        Train: details.Dataset.SampleCounts.Train,
                        Val: details.Dataset.SampleCounts.Val,
                        Test: details.Dataset.SampleCounts.Test)),
            Configuration: new TrainingRunConfigurationApiResponse(
                TrainingMode: details.Configuration.TrainingMode,
                TrainingProfileName: details.Configuration.TrainingProfileName,
                AugmentationProfileName: details.Configuration.AugmentationProfileName,
                BenchmarkName: details.Configuration.BenchmarkName,
                Seed: details.Configuration.Seed,
                EffectiveParameters: details.Configuration.EffectiveParameters is null
                    ? null
                    : ToTrainingRunEffectiveParametersApiResponse(details.Configuration.EffectiveParameters),
                SourceRevision: details.Configuration.SourceRevision),
            Progress: ToTrainingRunProgressApiResponse(details.Progress),
            Report: ToTrainingRunReportApiResponse(details.Report),
            Warnings: details.Warnings);
    }

    private static TrainingRunModelReferenceApiResponse ToTrainingRunModelReferenceApiResponse(
        TrainingRunModelReferenceDto model)
    {
        return new TrainingRunModelReferenceApiResponse(
            Name: model.Name,
            DisplayName: model.DisplayName,
            SourceType: model.SourceType,
            SourceRunName: model.SourceRunName,
            ParentModelName: model.ParentModelName,
            InputProfile: model.InputProfile,
            CanUseForInference: model.CanUseForInference,
            CanStartTraining: model.CanStartTraining);
    }

    private static TrainingRunReportApiResponse ToTrainingRunReportApiResponse(TrainingRunReportDto report)
    {
        return new TrainingRunReportApiResponse(
            Status: report.Status,
            Summary: report.Summary is null
                ? null
                : new TrainingReportSummaryApiResponse(
                    Accuracy: report.Summary.Accuracy,
                    PrecisionMacro: report.Summary.PrecisionMacro,
                    RecallMacro: report.Summary.RecallMacro,
                    F1Macro: report.Summary.F1Macro,
                    TrainingDurationSeconds: report.Summary.TrainingDurationSeconds,
                    AverageInferenceTimeMs: report.Summary.AverageInferenceTimeMs),
            PerClassMetrics: report.PerClassMetrics
                .Select(metric => new TrainingClassMetricApiResponse(
                    Label: metric.Label,
                    Precision: metric.Precision,
                    Recall: metric.Recall,
                    F1: metric.F1,
                    Support: metric.Support))
                .ToArray(),
            History: report.History
                .Select(point => new TrainingMetricHistoryPointApiResponse(
                    Epoch: point.Epoch,
                    TrainLoss: point.TrainLoss,
                    ValidationLoss: point.ValidationLoss,
                    TrainAccuracy: point.TrainAccuracy,
                    ValidationAccuracy: point.ValidationAccuracy))
                .ToArray(),
            ConfusionMatrix: report.ConfusionMatrix is null
                ? null
                : new TrainingConfusionMatrixApiResponse(
                    ClassNames: report.ConfusionMatrix.ClassNames,
                    Matrix: report.ConfusionMatrix.Matrix));
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
            EffectiveParameters: result.EffectiveParameters is null
                ? null
                : ToTrainingRunEffectiveParametersApiResponse(result.EffectiveParameters),
            ProgressChannelUrl: result.ProgressChannelUrl);
    }

    private static TrainingRunListItemApiResponse ToTrainingRunListItemApiResponse(TrainingRunListItemDto item)
    {
        return new TrainingRunListItemApiResponse(
            RunName: item.RunName,
            Status: item.Status,
            CreatedAtUtc: item.CreatedAtUtc,
            UpdatedAtUtc: item.UpdatedAtUtc,
            StartedAtUtc: item.StartedAtUtc,
            FinishedAtUtc: item.FinishedAtUtc,
            BaseModelName: item.BaseModelName,
            ProducedModelName: item.ProducedModelName,
            ProcessedDatasetName: item.ProcessedDatasetName,
            TrainingMode: item.TrainingMode,
            TrainingProfileName: item.TrainingProfileName,
            AugmentationProfileName: item.AugmentationProfileName,
            BenchmarkName: item.BenchmarkName,
            EffectiveParameters: item.EffectiveParameters is null
                ? null
                : ToTrainingRunEffectiveParametersApiResponse(item.EffectiveParameters),
            ReportStatus: item.ReportStatus,
            Progress: ToTrainingRunProgressApiResponse(item.Progress),
            MetricsSummary: ToTrainingMetricsSummaryApiResponse(item.MetricsSummary),
            Warnings: item.Warnings);
    }

    private static TrainingRunEffectiveParametersApiResponse ToTrainingRunEffectiveParametersApiResponse(
        TrainingRunEffectiveParametersDto effectiveParameters)
    {
        return new TrainingRunEffectiveParametersApiResponse(
            Epochs: effectiveParameters.Epochs,
            LearningRate: effectiveParameters.LearningRate,
            BatchSize: effectiveParameters.BatchSize,
            EarlyStoppingPatience: effectiveParameters.EarlyStoppingPatience,
            LrSchedulerPatience: effectiveParameters.LrSchedulerPatience,
            LrSchedulerFactor: effectiveParameters.LrSchedulerFactor,
            FineTuningPolicy: effectiveParameters.FineTuningPolicy,
            UseBestCheckpoint: effectiveParameters.UseBestCheckpoint);
    }

    private static TrainingRunProgressApiResponse? ToTrainingRunProgressApiResponse(
        TrainingRunProgressDto? progress)
    {
        if (progress is null)
        {
            return null;
        }

        return new TrainingRunProgressApiResponse(
            Percent: progress.Percent,
            EpochCurrent: progress.Epoch,
            EpochTotal: progress.TotalEpochs,
            TrainLoss: progress.TrainLoss,
            ValidationLoss: progress.ValidationLoss,
            TrainAccuracy: progress.TrainAccuracy,
            ValidationAccuracy: progress.ValidationAccuracy,
            EtaSeconds: progress.EtaSeconds);
    }

    private static TrainingMetricsSummaryApiResponse? ToTrainingMetricsSummaryApiResponse(
        TrainingMetricsSummaryDto? metricsSummary)
    {
        if (metricsSummary is null)
        {
            return null;
        }

        return new TrainingMetricsSummaryApiResponse(
            Accuracy: metricsSummary.Accuracy,
            MacroF1: metricsSummary.MacroF1);
    }

    private static IActionResult MapValidationError(
        ValidationException exception,
        string defaultErrorType = CreateTrainingRunErrorTypes.InvalidRequest)
    {
        var failure = exception.Errors.FirstOrDefault();
        var errorType = failure?.ErrorCode ?? defaultErrorType;
        var message = failure?.ErrorMessage ?? "Nieprawidłowe dane wejściowe.";

        return new ObjectResult(new ErrorApiResponse(
            ErrorType: errorType,
            Message: message))
        {
            StatusCode = StatusCodes.Status400BadRequest
        };
    }
}
