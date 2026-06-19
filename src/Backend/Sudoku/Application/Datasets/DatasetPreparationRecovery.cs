using Sudoku.Application.Abstractions;
using Sudoku.Models.Datasets;

namespace Sudoku.Application.Datasets;

public sealed class DatasetPreparationRecovery : IDatasetPreparationRecovery
{
    private const string InterruptedFailureMessage =
        "Przygotowanie datasetu zostalo przerwane przez restart backendu przed zakonczeniem pracy w tle.";

    private readonly IDatasetPreparationsGateway _datasetPreparationsGateway;
    private readonly IDatasetPreparationExecutionScheduler _executionScheduler;
    private readonly TimeProvider _timeProvider;

    public DatasetPreparationRecovery(
        IDatasetPreparationsGateway datasetPreparationsGateway,
        IDatasetPreparationExecutionScheduler executionScheduler,
        TimeProvider timeProvider)
    {
        _datasetPreparationsGateway = datasetPreparationsGateway;
        _executionScheduler = executionScheduler;
        _timeProvider = timeProvider;
    }

    public async Task RecoverAsync(CancellationToken cancellationToken = default)
    {
        var preparations = await _datasetPreparationsGateway.ListAsync(cancellationToken);
        var queuedPreparations = preparations
            .Where(preparation => string.Equals(preparation.Status, DatasetPreparationStatus.Queued, StringComparison.OrdinalIgnoreCase))
            .OrderBy(preparation => preparation.CreatedAtUtc)
            .ToArray();
        var interruptedRunningPreparations = preparations
            .Where(preparation => string.Equals(preparation.Status, DatasetPreparationStatus.Running, StringComparison.OrdinalIgnoreCase))
            .OrderBy(preparation => preparation.UpdatedAtUtc ?? preparation.CreatedAtUtc)
            .ToArray();

        foreach (var queuedPreparation in queuedPreparations)
        {
            await _executionScheduler.ScheduleAsync(
                new DatasetPreparationWorkItemDto(queuedPreparation.PreparationName),
                cancellationToken);
        }

        foreach (var interruptedPreparation in interruptedRunningPreparations)
        {
            await MarkInterruptedPreparationAsFailedAsync(interruptedPreparation, cancellationToken);
        }
    }

    private async Task MarkInterruptedPreparationAsFailedAsync(
        DatasetPreparationMetadataDto metadata,
        CancellationToken cancellationToken)
    {
        var warnings = new List<string>
        {
            CreateDatasetPreparationErrorTypes.PreparationInterrupted
        };

        try
        {
            await _datasetPreparationsGateway.CleanupGeneratedContentAsync(metadata.PreparationName, cancellationToken);
        }
        catch (Exception exception)
        {
            warnings.Add(CreateDatasetPreparationErrorTypes.PreparationCleanupPartial);
            _ = exception;
        }

        var failedAtUtc = _timeProvider.GetUtcNow();
        var failedMetadata = metadata with
        {
            Status = DatasetPreparationStatus.Failed,
            UpdatedAtUtc = failedAtUtc,
            FinishedAtUtc = failedAtUtc,
            FailureErrorType = CreateDatasetPreparationErrorTypes.PreparationInterrupted,
            FailureMessage = InterruptedFailureMessage,
            Warnings = MergeWarnings(metadata.Warnings, warnings)
        };

        await _datasetPreparationsGateway.UpdateAsync(failedMetadata, cancellationToken);
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
