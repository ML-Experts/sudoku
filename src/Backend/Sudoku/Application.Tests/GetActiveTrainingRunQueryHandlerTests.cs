using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Trainings;

namespace Application.Tests;

public sealed class GetActiveTrainingRunQueryHandlerTests
{
    private static readonly DateTimeOffset FixedNow = DateTimeOffset.Parse("2026-05-24T18:00:00Z");

    [Fact]
    public async Task Handle_ReturnsNoActiveRun_WhenOnlyCancellingRunIsStale()
    {
        var trainingRunsGateway = new InMemoryTrainingRunsGateway(
            new TrainingRunMetadataDto(
                RunName: "stale-run",
                Status: "cancelling",
                CreatedAtUtc: FixedNow.AddMinutes(-30),
                BaseModelName: "base-model",
                ProducedModelName: "produced-model",
                ProcessedDatasetName: "digits",
                TrainingMode: "fineTuning",
                TrainingProfileName: "cnn-default-v1",
                AugmentationProfileName: "digits-light-v1",
                BenchmarkName: "sudoku-benchmark-v1",
                Seed: 1234,
                ProgressChannelUrl: "/ws/trainings/stale-run",
                UpdatedAtUtc: FixedNow.AddMinutes(-15),
                Stage: "evaluation",
                LastAcceptedSequence: 10,
                LastEventType: "statusChanged",
                LastEventMessage: "Training evaluation started.",
                LastEventOccurredAtUtc: FixedNow.AddMinutes(-15)));
        var recovery = CreateRecovery(trainingRunsGateway);
        var handler = new GetActiveTrainingRunQueryHandler(trainingRunsGateway, recovery);

        var result = await handler.Handle(new GetActiveTrainingRunQuery(), CancellationToken.None);

        Assert.False(result.HasActiveRun);
        Assert.Null(result.Run);
        Assert.Equal("cancelled", trainingRunsGateway.Items["stale-run"].Status);
        Assert.Equal("finished", trainingRunsGateway.Items["stale-run"].Stage);
    }

    [Fact]
    public async Task Handle_ReturnsActiveRun_WhenCancellingRunIsStillFresh()
    {
        var trainingRunsGateway = new InMemoryTrainingRunsGateway(
            new TrainingRunMetadataDto(
                RunName: "fresh-run",
                Status: "cancelling",
                CreatedAtUtc: FixedNow.AddMinutes(-5),
                BaseModelName: "base-model",
                ProducedModelName: "produced-model",
                ProcessedDatasetName: "digits",
                TrainingMode: "fineTuning",
                TrainingProfileName: "cnn-default-v1",
                AugmentationProfileName: "digits-light-v1",
                BenchmarkName: "sudoku-benchmark-v1",
                Seed: 1234,
                ProgressChannelUrl: "/ws/trainings/fresh-run",
                UpdatedAtUtc: FixedNow.AddMinutes(-1),
                Stage: "evaluation",
                LastAcceptedSequence: 10,
                LastEventType: "statusChanged",
                LastEventMessage: "Training evaluation started.",
                LastEventOccurredAtUtc: FixedNow.AddMinutes(-1)));
        var recovery = CreateRecovery(trainingRunsGateway);
        var handler = new GetActiveTrainingRunQueryHandler(trainingRunsGateway, recovery);

        var result = await handler.Handle(new GetActiveTrainingRunQuery(), CancellationToken.None);

        Assert.True(result.HasActiveRun);
        Assert.NotNull(result.Run);
        Assert.Equal("fresh-run", result.Run!.RunName);
        Assert.Equal("cancelling", result.Run.Status);
    }

    private static TrainingRunCancellationRecovery CreateRecovery(
        InMemoryTrainingRunsGateway trainingRunsGateway)
    {
        return new TrainingRunCancellationRecovery(
            trainingRunsGateway,
            new StubTrainingArtifactsCleanupGateway(),
            new NoOpTrainingRunEventPublisher(),
            new InMemoryTrainingRunEventLockProvider(),
            Options.Create(new TrainingRecoveryOptions
            {
                StaleCancellingTimeoutSeconds = 300
            }),
            new FixedTimeProvider(FixedNow));
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
        public Task<IReadOnlyList<string>> CleanupFailedOrCancelledRunAsync(
            TrainingRunMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            return Task.FromResult<IReadOnlyList<string>>(Array.Empty<string>());
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
