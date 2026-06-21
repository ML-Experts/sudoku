using MediatR;
using Sudoku.Application.Abstractions;
using Sudoku.Application.ModelsRegistry;
using Sudoku.Application.Storage;
using Sudoku.Models.Trainings;

namespace Sudoku.Application.Trainings;

public sealed class RecordTrainingRunEventCommandHandler
    : IRequestHandler<RecordTrainingRunEventCommand, RecordTrainingRunEventResultDto>
{
    private const string AcceptedDisposition = "accepted";
    private const string DuplicateDisposition = "duplicate";
    private const string IgnoredTerminalStateDisposition = "ignored_terminal_state";

    private readonly ITrainingRunsGateway _trainingRunsGateway;
    private readonly IModelsRegistryGateway _modelsRegistryGateway;
    private readonly ITrainingArtifactsCleanupGateway _trainingArtifactsCleanupGateway;
    private readonly ITrainingRunEventPublisher _trainingRunEventPublisher;
    private readonly ITrainingRunEventLockProvider _trainingRunEventLockProvider;
    private readonly TimeProvider _timeProvider;

    public RecordTrainingRunEventCommandHandler(
        ITrainingRunsGateway trainingRunsGateway,
        IModelsRegistryGateway modelsRegistryGateway,
        ITrainingArtifactsCleanupGateway trainingArtifactsCleanupGateway,
        ITrainingRunEventPublisher trainingRunEventPublisher,
        ITrainingRunEventLockProvider trainingRunEventLockProvider,
        TimeProvider timeProvider)
    {
        _trainingRunsGateway = trainingRunsGateway;
        _modelsRegistryGateway = modelsRegistryGateway;
        _trainingArtifactsCleanupGateway = trainingArtifactsCleanupGateway;
        _trainingRunEventPublisher = trainingRunEventPublisher;
        _trainingRunEventLockProvider = trainingRunEventLockProvider;
        _timeProvider = timeProvider;
    }

    public async Task<RecordTrainingRunEventResultDto> Handle(
        RecordTrainingRunEventCommand request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.RunName)
            || string.IsNullOrWhiteSpace(request.EventType)
            || string.IsNullOrWhiteSpace(request.Status))
        {
            throw new InvalidOperationException("RecordTrainingRunEventCommand must be validated before handler execution.");
        }

        var runName = request.RunName.Trim();
        await using var runLock = await _trainingRunEventLockProvider.AcquireAsync(runName, cancellationToken);

        var metadata = await _trainingRunsGateway.GetByRunNameAsync(runName, cancellationToken);
        if (metadata is null)
        {
            throw new TrainingRunNotFoundException(runName);
        }

        if (metadata.LastAcceptedSequence is not null
            && request.Sequence <= metadata.LastAcceptedSequence.Value)
        {
            return ToResult(metadata, DuplicateDisposition);
        }

        if (TrainingRunStatus.IsTerminal(metadata.Status))
        {
            return HandleEventForTerminalRun(metadata, request);
        }

        var nextMetadata = await ApplyEventAsync(metadata, request, cancellationToken);

        try
        {
            await _trainingRunsGateway.UpdateAsync(nextMetadata, cancellationToken);
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidOperationException)
        {
            throw new TrainingRunEventPersistenceException(
                "Nie udało się zapisać metadanych eventu treningowego.",
                exception);
        }

        await _trainingRunEventPublisher.PublishAsync(nextMetadata, cancellationToken);
        return ToResult(nextMetadata, AcceptedDisposition);
    }

    private RecordTrainingRunEventResultDto HandleEventForTerminalRun(
        TrainingRunMetadataDto metadata,
        RecordTrainingRunEventCommand request)
    {
        if (request.EventType is TrainingRunEventType.Progress or TrainingRunEventType.StatusChanged)
        {
            return ToResult(metadata, IgnoredTerminalStateDisposition);
        }

        throw new TrainingRunEventConflictException(
            $"Run {metadata.RunName} jest już w stanie terminalnym {metadata.Status}.");
    }

    private async Task<TrainingRunMetadataDto> ApplyEventAsync(
        TrainingRunMetadataDto metadata,
        RecordTrainingRunEventCommand request,
        CancellationToken cancellationToken)
    {
        var nextStatus = ResolveNextStatus(metadata, request);
        var nextMetadata = metadata with
        {
            Status = nextStatus,
            Stage = request.Stage?.Trim(),
            UpdatedAtUtc = _timeProvider.GetUtcNow(),
            LastAcceptedSequence = request.Sequence,
            LastEventType = request.EventType,
            LastEventMessage = string.IsNullOrWhiteSpace(request.Message) ? null : request.Message.Trim(),
            LastEventOccurredAtUtc = request.OccurredAtUtc,
            StartedAtUtc = ResolveStartedAtUtc(metadata, nextStatus, request.OccurredAtUtc),
            Progress = request.Progress ?? metadata.Progress,
            Warnings = MergeWarnings(metadata.Warnings, request.Warnings)
        };

        return request.EventType switch
        {
            TrainingRunEventType.Completed => await ApplyCompletedEventAsync(nextMetadata, request, cancellationToken),
            TrainingRunEventType.Failed => await ApplyFailedEventAsync(nextMetadata, request, cancellationToken),
            TrainingRunEventType.Cancelled => await ApplyCancelledEventAsync(nextMetadata, request, cancellationToken),
            _ => nextMetadata
        };
    }

    private async Task<TrainingRunMetadataDto> ApplyCompletedEventAsync(
        TrainingRunMetadataDto metadata,
        RecordTrainingRunEventCommand request,
        CancellationToken cancellationToken)
    {
        var result = request.Result
                     ?? throw new TrainingRunEventInvalidTransitionException("Event completed wymaga sekcji result.");

        if (!string.Equals(result.ProducedModelName, metadata.ProducedModelName, StringComparison.Ordinal))
        {
            throw new TrainingRunEventInvalidTransitionException(
                "ProducedModelName w evencie nie odpowiada metadanym runu.");
        }

        if (string.IsNullOrWhiteSpace(result.PrimaryArtifactRelativePath))
        {
            throw new TrainingRunEventInvalidTransitionException(
                "Event completed wymaga primaryArtifactRelativePath.");
        }

        var reportStatus = ResolveReportStatus(result.ReportStatus);
        var canUseProducedModelForInference = result.CanUseProducedModelForInference
                                             ?? throw new TrainingRunEventInvalidTransitionException(
                                                 "Event completed wymaga canUseProducedModelForInference.");
        var baseModel = await _modelsRegistryGateway.GetByNameAsync(metadata.BaseModelName, cancellationToken)
                        ?? throw new TrainingRunEventInvalidTransitionException(
                            "Nie znaleziono modelu bazowego powiązanego z runem.");

        try
        {
            await _modelsRegistryGateway.FinalizeTrainedModelAsync(
                new FinalizeTrainedModelManifestDto(
                    Name: metadata.ProducedModelName,
                    DisplayName: metadata.ProducedModelName,
                    SourceRunName: metadata.RunName,
                    ParentModelName: metadata.BaseModelName,
                    TrainingMode: metadata.TrainingMode,
                    Framework: RequireTechnicalModelField(baseModel.Framework, "framework"),
                    ArchitectureType: RequireTechnicalModelField(baseModel.ArchitectureType, "architecture.type"),
                    ArchitectureFamily: RequireTechnicalModelField(baseModel.ArchitectureFamily, "architecture.family"),
                    ArchitectureNumClasses: RequireTechnicalModelField(
                        baseModel.ArchitectureNumClasses,
                        "architecture.numClasses"),
                    ArchitectureInputChannels: RequireTechnicalModelField(
                        baseModel.ArchitectureInputChannels,
                        "architecture.inputChannels"),
                    ArchitectureInputHeight: RequireTechnicalModelField(
                        baseModel.ArchitectureInputHeight,
                        "architecture.inputHeight"),
                    ArchitectureInputWidth: RequireTechnicalModelField(
                        baseModel.ArchitectureInputWidth,
                        "architecture.inputWidth"),
                    InputProfile: baseModel.InputProfile,
                    TrainingProfileName: metadata.TrainingProfileName,
                    AugmentationProfileName: metadata.AugmentationProfileName,
                    PrimaryArtifactRelativePath: result.PrimaryArtifactRelativePath.Trim(),
                    ArtifactFormat: RequireTechnicalModelField(baseModel.ArtifactFormat, "artifacts.format"),
                    CanUseForInference: canUseProducedModelForInference,
                    CreatedAtUtc: request.OccurredAtUtc),
                cancellationToken);
        }
        catch (FileStorageItemNotFoundException exception)
        {
            throw new TrainingRunEventArtifactNotReadyException(exception.Message);
        }
        catch (InvalidDataException exception)
        {
            throw new TrainingRunEventInvalidTransitionException(exception.Message);
        }

        return metadata with
        {
            Status = TrainingRunStatus.Succeeded,
            FinishedAtUtc = request.OccurredAtUtc,
            ReportStatus = reportStatus,
            ReportRelativePath = result.ReportRelativePath,
            PrimaryArtifactRelativePath = result.PrimaryArtifactRelativePath,
            ReportArtifacts = new TrainingReportArtifactsDto(
                SummaryRelativePath: result.SummaryRelativePath,
                MetricsRelativePath: result.MetricsRelativePath,
                ConfusionMatrixRelativePath: result.ConfusionMatrixRelativePath),
            MetricsSummary = result.MetricsSummary
        };
    }

    private async Task<TrainingRunMetadataDto> ApplyFailedEventAsync(
        TrainingRunMetadataDto metadata,
        RecordTrainingRunEventCommand request,
        CancellationToken cancellationToken)
    {
        var cleanupWarnings = await _trainingArtifactsCleanupGateway.CleanupFailedOrCancelledRunAsync(
            metadata,
            cancellationToken);

        return metadata with
        {
            Status = TrainingRunStatus.Failed,
            FinishedAtUtc = request.OccurredAtUtc,
            FailureReason = ResolveFailureMessage(request),
            FailureErrorType = string.IsNullOrWhiteSpace(request.Failure?.ErrorType)
                ? null
                : request.Failure.ErrorType.Trim(),
            CleanupWarnings = MergeWarnings(metadata.CleanupWarnings, cleanupWarnings)
        };
    }

    private async Task<TrainingRunMetadataDto> ApplyCancelledEventAsync(
        TrainingRunMetadataDto metadata,
        RecordTrainingRunEventCommand request,
        CancellationToken cancellationToken)
    {
        var cleanupWarnings = await _trainingArtifactsCleanupGateway.CleanupFailedOrCancelledRunAsync(
            metadata,
            cancellationToken);

        return metadata with
        {
            Status = TrainingRunStatus.Cancelled,
            FinishedAtUtc = request.OccurredAtUtc,
            CleanupWarnings = MergeWarnings(metadata.CleanupWarnings, cleanupWarnings)
        };
    }

    private static string ResolveNextStatus(
        TrainingRunMetadataDto metadata,
        RecordTrainingRunEventCommand request)
    {
        var nextStatus = request.EventType switch
        {
            TrainingRunEventType.Completed => TrainingRunStatus.Succeeded,
            TrainingRunEventType.Failed => TrainingRunStatus.Failed,
            TrainingRunEventType.Cancelled => TrainingRunStatus.Cancelled,
            _ => request.Status!.Trim()
        };

        EnsureAllowedTransition(metadata.Status, nextStatus, metadata.RunName);
        return nextStatus;
    }

    private static void EnsureAllowedTransition(string currentStatus, string nextStatus, string runName)
    {
        if (string.Equals(currentStatus, nextStatus, StringComparison.Ordinal)
            || string.Equals(currentStatus, TrainingRunStatus.Starting, StringComparison.Ordinal)
                && nextStatus is TrainingRunStatus.Queued
                    or TrainingRunStatus.Running
                    or TrainingRunStatus.Succeeded
                    or TrainingRunStatus.Failed
                    or TrainingRunStatus.Cancelled
            || string.Equals(currentStatus, TrainingRunStatus.Queued, StringComparison.Ordinal)
                && nextStatus is TrainingRunStatus.Running
                    or TrainingRunStatus.Cancelling
                    or TrainingRunStatus.Succeeded
                    or TrainingRunStatus.Failed
                    or TrainingRunStatus.Cancelled
            || string.Equals(currentStatus, TrainingRunStatus.Running, StringComparison.Ordinal)
                && nextStatus is TrainingRunStatus.Cancelling
                    or TrainingRunStatus.Succeeded
                    or TrainingRunStatus.Failed
                    or TrainingRunStatus.Cancelled
            || string.Equals(currentStatus, TrainingRunStatus.Cancelling, StringComparison.Ordinal)
                && nextStatus is TrainingRunStatus.Cancelled
                    or TrainingRunStatus.Failed
                    or TrainingRunStatus.Succeeded)
        {
            return;
        }

        throw new TrainingRunEventInvalidTransitionException(
            $"Niedozwolona zmiana statusu runu {runName}: {currentStatus} -> {nextStatus}.");
    }

    private static DateTimeOffset? ResolveStartedAtUtc(
        TrainingRunMetadataDto metadata,
        string nextStatus,
        DateTimeOffset occurredAtUtc)
    {
        if (metadata.StartedAtUtc is not null)
        {
            return metadata.StartedAtUtc;
        }

        return string.Equals(nextStatus, TrainingRunStatus.Running, StringComparison.Ordinal)
            ? occurredAtUtc
            : null;
    }

    private static string ResolveReportStatus(string? reportStatus)
    {
        if (string.IsNullOrWhiteSpace(reportStatus))
        {
            return TrainingReportStatus.Ready;
        }

        var trimmedStatus = reportStatus.Trim();
        if (trimmedStatus is TrainingReportStatus.Ready
            or TrainingReportStatus.Missing
            or TrainingReportStatus.Corrupted)
        {
            return trimmedStatus;
        }

        throw new TrainingRunEventInvalidTransitionException("Event completed zawiera niedozwolony reportStatus.");
    }

    private static string RequireTechnicalModelField(string? value, string fieldName)
    {
        return string.IsNullOrWhiteSpace(value)
            ? throw new TrainingRunEventInvalidTransitionException(
                $"Model bazowy nie zawiera wymaganego pola technicznego {fieldName}.")
            : value.Trim();
    }

    private static string? ResolveFailureMessage(RecordTrainingRunEventCommand request)
    {
        if (!string.IsNullOrWhiteSpace(request.Failure?.Message))
        {
            return request.Failure.Message.Trim();
        }

        return string.IsNullOrWhiteSpace(request.Message) ? null : request.Message.Trim();
    }

    private static int RequireTechnicalModelField(int? value, string fieldName)
    {
        return value
               ?? throw new TrainingRunEventInvalidTransitionException(
                   $"Model bazowy nie zawiera wymaganego pola technicznego {fieldName}.");
    }

    private static IReadOnlyList<string> MergeWarnings(
        IReadOnlyList<string>? currentWarnings,
        IReadOnlyList<string>? newWarnings)
    {
        return (currentWarnings ?? Array.Empty<string>())
            .Concat(newWarnings ?? Array.Empty<string>())
            .Where(warning => !string.IsNullOrWhiteSpace(warning))
            .Select(warning => warning.Trim())
            .Distinct(StringComparer.Ordinal)
            .ToArray();
    }

    private static RecordTrainingRunEventResultDto ToResult(
        TrainingRunMetadataDto metadata,
        string disposition)
    {
        return new RecordTrainingRunEventResultDto(
            Accepted: true,
            RunName: metadata.RunName,
            Status: metadata.Status,
            LastAcceptedSequence: metadata.LastAcceptedSequence,
            Disposition: disposition);
    }
}
