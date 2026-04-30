using MediatR;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Ml;
using Sudoku.Application.Storage;
using Sudoku.Models.Trainings;

namespace Sudoku.Application.Trainings;

public sealed class CancelTrainingRunCommandHandler
    : IRequestHandler<CancelTrainingRunCommand, CancelTrainingRunCommandResultDto>
{
    private const string UserRequestedReason = "user_requested";
    private const string CancelRequestDeliveryFailedWarning = "cancel_request_delivery_failed";

    private readonly ITrainingRunsGateway _trainingRunsGateway;
    private readonly IMlTrainingsGateway _mlTrainingsGateway;
    private readonly ITrainingRunEventPublisher _trainingRunEventPublisher;
    private readonly ITrainingRunEventLockProvider _trainingRunEventLockProvider;
    private readonly TimeProvider _timeProvider;

    public CancelTrainingRunCommandHandler(
        ITrainingRunsGateway trainingRunsGateway,
        IMlTrainingsGateway mlTrainingsGateway,
        ITrainingRunEventPublisher trainingRunEventPublisher,
        ITrainingRunEventLockProvider trainingRunEventLockProvider,
        TimeProvider timeProvider)
    {
        _trainingRunsGateway = trainingRunsGateway;
        _mlTrainingsGateway = mlTrainingsGateway;
        _trainingRunEventPublisher = trainingRunEventPublisher;
        _trainingRunEventLockProvider = trainingRunEventLockProvider;
        _timeProvider = timeProvider;
    }

    public async Task<CancelTrainingRunCommandResultDto> Handle(
        CancelTrainingRunCommand request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.RunName))
        {
            throw new InvalidOperationException("CancelTrainingRunCommand must be validated before handler execution.");
        }

        var runName = request.RunName.Trim();
        await using var runLock = await _trainingRunEventLockProvider.AcquireAsync(runName, cancellationToken);

        var metadata = await _trainingRunsGateway.GetByRunNameAsync(runName, cancellationToken);
        if (metadata is null)
        {
            return CreateResult(
                runName,
                status: null,
                progressChannelUrl: null,
                disposition: CancelTrainingRunDispositions.NotFound);
        }

        if (TrainingRunStatus.IsTerminal(metadata.Status))
        {
            return CreateResult(
                runName,
                metadata.Status,
                metadata.ProgressChannelUrl,
                CancelTrainingRunDispositions.AlreadyFinished);
        }

        EnsureSingleActiveRunInvariant(metadata, await _trainingRunsGateway.ListAsync(cancellationToken));

        if (string.Equals(metadata.Status, TrainingRunStatus.Cancelling, StringComparison.OrdinalIgnoreCase))
        {
            if (HasWarning(metadata.Warnings, CancelRequestDeliveryFailedWarning))
            {
                await RequestMlCancellationAsync(runName, cancellationToken);
                return CreateResult(
                    runName,
                    metadata.Status,
                    metadata.ProgressChannelUrl,
                    CancelTrainingRunDispositions.Accepted);
            }

            return CreateResult(
                runName,
                metadata.Status,
                metadata.ProgressChannelUrl,
                CancelTrainingRunDispositions.Duplicate);
        }

        if (string.Equals(metadata.Status, TrainingRunStatus.Starting, StringComparison.OrdinalIgnoreCase))
        {
            return CreateResult(
                runName,
                metadata.Status,
                metadata.ProgressChannelUrl,
                CancelTrainingRunDispositions.StartNotConfirmed);
        }

        if (!TrainingRunStatus.CanRequestCancellation(metadata.Status))
        {
            return CreateResult(
                runName,
                metadata.Status,
                metadata.ProgressChannelUrl,
                CancelTrainingRunDispositions.NotActive);
        }

        var requestedAtUtc = _timeProvider.GetUtcNow();
        var cancellingMetadata = metadata with
        {
            Status = TrainingRunStatus.Cancelling,
            UpdatedAtUtc = requestedAtUtc
        };

        await UpdateMetadataAsync(cancellingMetadata, cancellationToken);
        await _trainingRunEventPublisher.PublishAsync(cancellingMetadata, cancellationToken);

        try
        {
            await RequestMlCancellationAsync(runName, cancellationToken);
        }
        catch (Exception exception) when (exception is MlOperationFailedException
                                         or MlServiceUnavailableException
                                         or MlServiceTimeoutException)
        {
            var metadataWithWarning = cancellingMetadata with
            {
                Warnings = MergeWarnings(cancellingMetadata.Warnings, CancelRequestDeliveryFailedWarning),
                UpdatedAtUtc = _timeProvider.GetUtcNow()
            };

            await UpdateMetadataAsync(metadataWithWarning, cancellationToken);
            throw;
        }

        return CreateResult(
            runName,
            TrainingRunStatus.Cancelling,
            cancellingMetadata.ProgressChannelUrl,
            CancelTrainingRunDispositions.Accepted);
    }

    private static void EnsureSingleActiveRunInvariant(
        TrainingRunMetadataDto requestedMetadata,
        IReadOnlyList<TrainingRunMetadataDto> runs)
    {
        var activeRuns = runs
            .Where(run => TrainingRunStatus.IsActive(run.Status))
            .ToArray();

        if (activeRuns.Length > 1)
        {
            throw new InvalidOperationException(
                "Detected more than one active training run. This violates the single active run invariant.");
        }

        if (activeRuns.Length == 1
            && !string.Equals(activeRuns[0].RunName, requestedMetadata.RunName, StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                "Detected active training run mismatch. This violates the single active run invariant.");
        }
    }

    private async Task UpdateMetadataAsync(
        TrainingRunMetadataDto metadata,
        CancellationToken cancellationToken)
    {
        try
        {
            await _trainingRunsGateway.UpdateAsync(metadata, cancellationToken);
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidOperationException
                                         or FileStorageItemNotFoundException)
        {
            throw new TrainingRunCancelPersistenceException(
                "Nie udało się zapisać metadanych anulowania runu treningowego.",
                exception);
        }
    }

    private static IReadOnlyList<string> MergeWarnings(
        IReadOnlyList<string>? warnings,
        string warning)
    {
        var existingWarnings = warnings ?? Array.Empty<string>();
        if (existingWarnings.Contains(warning, StringComparer.Ordinal))
        {
            return existingWarnings;
        }

        return existingWarnings
            .Concat(new[] { warning })
            .ToArray();
    }

    private static bool HasWarning(
        IReadOnlyList<string>? warnings,
        string warning)
    {
        return warnings?.Contains(warning, StringComparer.Ordinal) == true;
    }

    private async Task RequestMlCancellationAsync(
        string runName,
        CancellationToken cancellationToken)
    {
        await _mlTrainingsGateway.CancelTrainingAsync(
            new CancelMlTrainingRequestDto(
                RunName: runName,
                RequestedAtUtc: _timeProvider.GetUtcNow(),
                Reason: UserRequestedReason),
            cancellationToken);
    }

    private static CancelTrainingRunCommandResultDto CreateResult(
        string runName,
        string? status,
        string? progressChannelUrl,
        string disposition)
    {
        return new CancelTrainingRunCommandResultDto(
            RunName: runName,
            Status: status,
            RequestDisposition: disposition,
            Message: ResolveMessage(disposition),
            ProgressChannelUrl: progressChannelUrl);
    }

    private static string ResolveMessage(string disposition)
    {
        return disposition switch
        {
            CancelTrainingRunDispositions.Accepted => "Anulowanie runu zostało przyjęte.",
            CancelTrainingRunDispositions.Duplicate => "Run jest już w trakcie anulowania.",
            CancelTrainingRunDispositions.AlreadyFinished => "Run jest już zakończony i nie może zostać anulowany.",
            CancelTrainingRunDispositions.NotFound => "Nie znaleziono aktywnego runu o podanej nazwie.",
            CancelTrainingRunDispositions.NotActive => "Run nie jest aktywny i nie może zostać anulowany.",
            CancelTrainingRunDispositions.StartNotConfirmed => "Start runu nie został jeszcze potwierdzony; ponów anulowanie po aktualizacji statusu.",
            _ => "Żądanie anulowania runu zostało obsłużone."
        };
    }
}
