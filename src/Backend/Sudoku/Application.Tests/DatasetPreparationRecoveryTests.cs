using Sudoku.Application.Abstractions;
using Sudoku.Application.Datasets;

namespace Application.Tests;

public sealed class DatasetPreparationRecoveryTests
{
    private static readonly DateTimeOffset FixedNow = DateTimeOffset.Parse("2026-06-19T20:00:00Z");

    [Fact]
    public async Task RecoverAsync_RequeuesQueuedPreparations()
    {
        var gateway = new InMemoryDatasetPreparationsGateway([
            CreateMetadata("queued-preparation", "queued")
        ]);
        var scheduler = new RecordingDatasetPreparationExecutionScheduler();
        var recovery = new DatasetPreparationRecovery(
            gateway,
            scheduler,
            new FixedTimeProvider(FixedNow));

        await recovery.RecoverAsync(CancellationToken.None);

        Assert.Equal(["queued-preparation"], scheduler.ScheduledPreparationNames);
    }

    [Fact]
    public async Task RecoverAsync_MarksRunningPreparationAsFailed()
    {
        var gateway = new InMemoryDatasetPreparationsGateway([
            CreateMetadata("running-preparation", "running")
        ]);
        var recovery = new DatasetPreparationRecovery(
            gateway,
            new RecordingDatasetPreparationExecutionScheduler(),
            new FixedTimeProvider(FixedNow));

        await recovery.RecoverAsync(CancellationToken.None);

        var metadata = gateway.Items["running-preparation"];
        Assert.Equal("failed", metadata.Status);
        Assert.Equal(CreateDatasetPreparationErrorTypes.PreparationInterrupted, metadata.FailureErrorType);
        Assert.Contains(CreateDatasetPreparationErrorTypes.PreparationInterrupted, metadata.Warnings);
    }

    private static DatasetPreparationMetadataDto CreateMetadata(string preparationName, string status)
    {
        return new DatasetPreparationMetadataDto(
            PreparationName: preparationName,
            Status: status,
            CreatedAtUtc: FixedNow.AddMinutes(-5),
            UpdatedAtUtc: FixedNow.AddMinutes(-1),
            StartedAtUtc: status == "running" ? FixedNow.AddMinutes(-4) : null,
            FinishedAtUtc: null,
            Sources: [new CreateDatasetPreparationSourceDto("v1_training", "board")],
            SourceReports: [new DatasetPreparationSourceReportDto("v1_training", "board", 0, 0, 0)],
            Warnings: [],
            FailureErrorType: null,
            FailureMessage: null);
    }

    private sealed class InMemoryDatasetPreparationsGateway : IDatasetPreparationsGateway
    {
        public InMemoryDatasetPreparationsGateway(IReadOnlyList<DatasetPreparationMetadataDto> items)
        {
            foreach (var item in items)
            {
                Items[item.PreparationName] = item;
            }
        }

        public Dictionary<string, DatasetPreparationMetadataDto> Items { get; } = new(StringComparer.Ordinal);

        public Task<IReadOnlyList<DatasetPreparationMetadataDto>> ListAsync(CancellationToken cancellationToken = default)
        {
            return Task.FromResult<IReadOnlyList<DatasetPreparationMetadataDto>>(Items.Values.ToArray());
        }

        public Task<DatasetPreparationMetadataDto?> GetByNameAsync(
            string preparationName,
            CancellationToken cancellationToken = default)
        {
            Items.TryGetValue(preparationName, out var metadata);
            return Task.FromResult(metadata);
        }

        public Task<bool> TryCreateAsync(
            DatasetPreparationMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            Items[metadata.PreparationName] = metadata;
            return Task.FromResult(true);
        }

        public Task UpdateAsync(
            DatasetPreparationMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            Items[metadata.PreparationName] = metadata;
            return Task.CompletedTask;
        }

        public Task CleanupGeneratedContentAsync(
            string preparationName,
            CancellationToken cancellationToken = default)
        {
            return Task.CompletedTask;
        }
    }

    private sealed class RecordingDatasetPreparationExecutionScheduler : IDatasetPreparationExecutionScheduler
    {
        public List<string> ScheduledPreparationNames { get; } = [];

        public Task ScheduleAsync(
            DatasetPreparationWorkItemDto workItem,
            CancellationToken cancellationToken = default)
        {
            ScheduledPreparationNames.Add(workItem.PreparationName);
            return Task.CompletedTask;
        }
    }

    private sealed class FixedTimeProvider : TimeProvider
    {
        private readonly DateTimeOffset _utcNow;

        public FixedTimeProvider(DateTimeOffset utcNow)
        {
            _utcNow = utcNow;
        }

        public override DateTimeOffset GetUtcNow()
        {
            return _utcNow;
        }
    }
}
