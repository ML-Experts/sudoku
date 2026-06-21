using Sudoku.Application.Abstractions;
using Sudoku.Application.ModelsRegistry;
using Sudoku.Application.Trainings;

namespace Application.Tests;

public sealed class RecordTrainingRunEventCommandHandlerTests
{
    private static readonly DateTimeOffset FixedNow = DateTimeOffset.Parse("2026-06-18T18:20:00Z");

    [Fact]
    public async Task Handle_AcceptsFailedTerminalEvent_WhenRunIsQueued()
    {
        var trainingRunsGateway = new InMemoryTrainingRunsGateway(CreateMetadata("queued"));
        var cleanupGateway = new StubTrainingArtifactsCleanupGateway();
        var publisher = new RecordingTrainingRunEventPublisher();
        var handler = CreateHandler(
            trainingRunsGateway: trainingRunsGateway,
            cleanupGateway: cleanupGateway,
            publisher: publisher);

        var result = await handler.Handle(
            CreateCommand(
                eventType: "failed",
                status: "failed",
                stage: "training",
                message: "Training failed before first running event.",
                failure: new TrainingRunFailureDto(
                    ErrorType: "training_run_failed",
                    Message: "Training failed before first running event.",
                    CanUseProducedModelForInference: false)),
            CancellationToken.None);

        Assert.True(result.Accepted);
        Assert.Equal("accepted", result.Disposition);

        var metadata = trainingRunsGateway.Items["run-1"];
        Assert.Equal("failed", metadata.Status);
        Assert.Equal(1L, metadata.LastAcceptedSequence);
        Assert.Equal("failed", metadata.LastEventType);
        Assert.Equal("Training failed before first running event.", metadata.FailureReason);
        Assert.Equal(1, cleanupGateway.Calls);
        Assert.Single(publisher.PublishedMetadata);
    }

    [Fact]
    public async Task Handle_AcceptsCancelledTerminalEvent_WhenRunIsStarting()
    {
        var trainingRunsGateway = new InMemoryTrainingRunsGateway(CreateMetadata("starting"));
        var cleanupGateway = new StubTrainingArtifactsCleanupGateway();
        var publisher = new RecordingTrainingRunEventPublisher();
        var handler = CreateHandler(
            trainingRunsGateway: trainingRunsGateway,
            cleanupGateway: cleanupGateway,
            publisher: publisher);

        var result = await handler.Handle(
            CreateCommand(
                eventType: "cancelled",
                status: "cancelled",
                stage: "finished",
                message: "Training cancelled on user request."),
            CancellationToken.None);

        Assert.True(result.Accepted);
        Assert.Equal("accepted", result.Disposition);

        var metadata = trainingRunsGateway.Items["run-1"];
        Assert.Equal("cancelled", metadata.Status);
        Assert.Equal("finished", metadata.Stage);
        Assert.Equal(1L, metadata.LastAcceptedSequence);
        Assert.Equal("cancelled", metadata.LastEventType);
        Assert.Equal(1, cleanupGateway.Calls);
        Assert.Single(publisher.PublishedMetadata);
    }

    private static RecordTrainingRunEventCommandHandler CreateHandler(
        InMemoryTrainingRunsGateway? trainingRunsGateway = null,
        StubTrainingArtifactsCleanupGateway? cleanupGateway = null,
        RecordingTrainingRunEventPublisher? publisher = null)
    {
        return new RecordTrainingRunEventCommandHandler(
            trainingRunsGateway ?? new InMemoryTrainingRunsGateway(CreateMetadata("queued")),
            new StubModelsRegistryGateway(),
            cleanupGateway ?? new StubTrainingArtifactsCleanupGateway(),
            publisher ?? new RecordingTrainingRunEventPublisher(),
            new InMemoryTrainingRunEventLockProvider(),
            new FixedTimeProvider(FixedNow));
    }

    private static TrainingRunMetadataDto CreateMetadata(string status)
    {
        return new TrainingRunMetadataDto(
            RunName: "run-1",
            Status: status,
            CreatedAtUtc: FixedNow.AddMinutes(-2),
            BaseModelName: "cnn-baseline",
            ProducedModelName: "run-1",
            ProcessedDatasetName: "dataset-1",
            TrainingMode: "fineTuning",
            TrainingProfileName: "cnn-default-v1",
            AugmentationProfileName: "digits-light-v1",
            BenchmarkName: "sudoku-benchmark-v1",
            Seed: 1234,
            ProgressChannelUrl: "/ws/trainings/run-1",
            UpdatedAtUtc: FixedNow.AddMinutes(-1));
    }

    private static RecordTrainingRunEventCommand CreateCommand(
        string eventType,
        string status,
        string stage,
        string message,
        TrainingRunFailureDto? failure = null)
    {
        return new RecordTrainingRunEventCommand(
            RunName: "run-1",
            Sequence: 1,
            EventType: eventType,
            Status: status,
            Stage: stage,
            OccurredAtUtc: FixedNow,
            Message: message,
            Progress: null,
            Result: null,
            Failure: failure,
            Warnings: Array.Empty<string>());
    }

    private sealed class InMemoryTrainingRunsGateway : ITrainingRunsGateway
    {
        public Dictionary<string, TrainingRunMetadataDto> Items { get; } = new(StringComparer.Ordinal);

        public InMemoryTrainingRunsGateway(params TrainingRunMetadataDto[] items)
        {
            foreach (var item in items)
            {
                Items[item.RunName] = item;
            }
        }

        public Task<IReadOnlyList<TrainingRunMetadataDto>> ListAsync(CancellationToken cancellationToken = default)
        {
            return Task.FromResult<IReadOnlyList<TrainingRunMetadataDto>>(Items.Values.ToArray());
        }

        public Task<TrainingRunMetadataDto?> GetByRunNameAsync(
            string runName,
            CancellationToken cancellationToken = default)
        {
            Items.TryGetValue(runName, out var metadata);
            return Task.FromResult(metadata);
        }

        public Task<bool> TryCreateAsync(
            TrainingRunMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            var created = Items.TryAdd(metadata.RunName, metadata);
            return Task.FromResult(created);
        }

        public Task UpdateAsync(
            TrainingRunMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            Items[metadata.RunName] = metadata;
            return Task.CompletedTask;
        }

        public Task DeleteAsync(string runName, CancellationToken cancellationToken = default)
        {
            Items.Remove(runName);
            return Task.CompletedTask;
        }
    }

    private sealed class StubTrainingArtifactsCleanupGateway : ITrainingArtifactsCleanupGateway
    {
        public int Calls { get; private set; }

        public Task<IReadOnlyList<string>> CleanupFailedOrCancelledRunAsync(
            TrainingRunMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            Calls++;
            return Task.FromResult<IReadOnlyList<string>>(Array.Empty<string>());
        }
    }

    private sealed class RecordingTrainingRunEventPublisher : ITrainingRunEventPublisher
    {
        public List<TrainingRunMetadataDto> PublishedMetadata { get; } = [];

        public Task PublishAsync(
            TrainingRunMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            PublishedMetadata.Add(metadata);
            return Task.CompletedTask;
        }
    }

    private sealed class StubModelsRegistryGateway : IModelsRegistryGateway
    {
        public Task<IReadOnlyList<RegistryModelManifestDto>> ListAsync(
            CancellationToken cancellationToken = default)
        {
            return Task.FromResult<IReadOnlyList<RegistryModelManifestDto>>(Array.Empty<RegistryModelManifestDto>());
        }

        public Task<RegistryModelManifestDto?> GetByNameAsync(
            string modelName,
            CancellationToken cancellationToken = default)
        {
            return Task.FromResult<RegistryModelManifestDto?>(null);
        }

        public Task FinalizeTrainedModelAsync(
            FinalizeTrainedModelManifestDto manifest,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }
    }

    private sealed class InMemoryTrainingRunEventLockProvider : ITrainingRunEventLockProvider
    {
        public ValueTask<IAsyncDisposable> AcquireAsync(
            string runName,
            CancellationToken cancellationToken = default)
        {
            return ValueTask.FromResult<IAsyncDisposable>(new NoOpAsyncDisposable());
        }
    }

    private sealed class NoOpAsyncDisposable : IAsyncDisposable
    {
        public ValueTask DisposeAsync()
        {
            return ValueTask.CompletedTask;
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
