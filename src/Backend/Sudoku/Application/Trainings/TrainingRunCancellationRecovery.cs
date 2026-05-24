using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Models.Trainings;

namespace Sudoku.Application.Trainings;

public sealed class TrainingRunCancellationRecovery : ITrainingRunCancellationRecovery
{
    private const string FinishedStage = "finished";
    private const string AutoCancelledWarning = "stale_cancelling_auto_cancelled";
    private const string AutoCancelledMessage =
        "Backend automatycznie zakonczyl run w statusie cancelled po przekroczeniu limitu dla cancelling.";

    private readonly ITrainingRunsGateway _trainingRunsGateway;
    private readonly ITrainingArtifactsCleanupGateway _trainingArtifactsCleanupGateway;
    private readonly ITrainingRunEventPublisher _trainingRunEventPublisher;
    private readonly ITrainingRunEventLockProvider _trainingRunEventLockProvider;
    private readonly TimeProvider _timeProvider;
    private readonly TrainingRecoveryOptions _options;

    public TrainingRunCancellationRecovery(
        ITrainingRunsGateway trainingRunsGateway,
        ITrainingArtifactsCleanupGateway trainingArtifactsCleanupGateway,
        ITrainingRunEventPublisher trainingRunEventPublisher,
        ITrainingRunEventLockProvider trainingRunEventLockProvider,
        IOptions<TrainingRecoveryOptions> options,
        TimeProvider timeProvider)
    {
        _trainingRunsGateway = trainingRunsGateway;
        _trainingArtifactsCleanupGateway = trainingArtifactsCleanupGateway;
        _trainingRunEventPublisher = trainingRunEventPublisher;
        _trainingRunEventLockProvider = trainingRunEventLockProvider;
        _timeProvider = timeProvider;
        _options = options.Value;
    }

    public async Task RecoverAsync(CancellationToken cancellationToken = default)
    {
        var runs = await _trainingRunsGateway.ListAsync(cancellationToken);
        var staleRuns = runs
            .Where(run => string.Equals(run.Status, TrainingRunStatus.Cancelling, StringComparison.OrdinalIgnoreCase))
            .Where(IsStaleCancellingRun)
            .OrderBy(run => GetLastActivityAtUtc(run))
            .ToArray();

        foreach (var staleRun in staleRuns)
        {
            await RecoverSingleRunAsync(staleRun.RunName, cancellationToken);
        }
    }

    private async Task RecoverSingleRunAsync(string runName, CancellationToken cancellationToken)
    {
        await using var runLock = await _trainingRunEventLockProvider.AcquireAsync(runName, cancellationToken);
        var metadata = await _trainingRunsGateway.GetByRunNameAsync(runName, cancellationToken);
        if (metadata is null || !string.Equals(metadata.Status, TrainingRunStatus.Cancelling, StringComparison.OrdinalIgnoreCase))
        {
            return;
        }

        if (!IsStaleCancellingRun(metadata))
        {
            return;
        }

        var finishedAtUtc = _timeProvider.GetUtcNow();
        var cleanupWarnings = await _trainingArtifactsCleanupGateway.CleanupFailedOrCancelledRunAsync(
            metadata,
            cancellationToken);
        var recoveredMetadata = metadata with
        {
            Status = TrainingRunStatus.Cancelled,
            Stage = FinishedStage,
            UpdatedAtUtc = finishedAtUtc,
            FinishedAtUtc = metadata.FinishedAtUtc ?? finishedAtUtc,
            LastAcceptedSequence = (metadata.LastAcceptedSequence ?? 0L) + 1L,
            LastEventType = TrainingRunEventType.Cancelled,
            LastEventMessage = AutoCancelledMessage,
            LastEventOccurredAtUtc = finishedAtUtc,
            Warnings = MergeWarnings(metadata.Warnings, new[] { AutoCancelledWarning }),
            CleanupWarnings = MergeWarnings(metadata.CleanupWarnings, cleanupWarnings)
        };

        await _trainingRunsGateway.UpdateAsync(recoveredMetadata, cancellationToken);
        await _trainingRunEventPublisher.PublishAsync(recoveredMetadata, cancellationToken);
    }

    private bool IsStaleCancellingRun(TrainingRunMetadataDto metadata)
    {
        var lastActivityAtUtc = GetLastActivityAtUtc(metadata);
        return _timeProvider.GetUtcNow() - lastActivityAtUtc
               >= TimeSpan.FromSeconds(_options.StaleCancellingTimeoutSeconds);
    }

    private static DateTimeOffset GetLastActivityAtUtc(TrainingRunMetadataDto metadata)
    {
        var candidates = new[]
        {
            metadata.CreatedAtUtc,
            metadata.UpdatedAtUtc ?? DateTimeOffset.MinValue,
            metadata.LastEventOccurredAtUtc ?? DateTimeOffset.MinValue
        };

        return candidates.Max();
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
}
