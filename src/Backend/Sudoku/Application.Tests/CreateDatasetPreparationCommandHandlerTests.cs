using MediatR;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Datasets;
using Sudoku.Application.Storage;

namespace Application.Tests;

public sealed class CreateDatasetPreparationCommandHandlerTests
{
    private static readonly DateTimeOffset FixedNow = DateTimeOffset.Parse("2026-06-19T18:42:11Z");

    [Fact]
    public async Task Handle_QueuesPreparationAndSchedulesBackgroundWork()
    {
        var gateway = new InMemoryDatasetPreparationsGateway();
        var scheduler = new RecordingDatasetPreparationExecutionScheduler();
        var handler = CreateHandler(
            sender: new StubSender(new ListRawDatasetCandidatesQueryResultDto(
                Items:
                [
                    new ListRawDatasetCandidateItemDto("v1_training", "board"),
                    new ListRawDatasetCandidateItemDto("mnist_train", "digit")
                ])),
            gateway: gateway,
            scheduler: scheduler);

        var result = await handler.Handle(
            new CreateDatasetPreparationCommand(
                PreparationName: "preparation-001",
                Sources:
                [
                    new CreateDatasetPreparationSourceDto("v1_training", "board"),
                    new CreateDatasetPreparationSourceDto("mnist_train", "digit")
                ]),
            CancellationToken.None);

        Assert.Equal("preparation-001", result.PreparationName);
        Assert.Equal("queued", result.Status);
        Assert.Equal(FixedNow, result.CreatedAtUtc);
        Assert.Equal(["preparation-001"], scheduler.ScheduledPreparationNames);

        var metadata = Assert.Single(gateway.Items.Values);
        Assert.Equal("queued", metadata.Status);
        Assert.Equal(FixedNow, metadata.CreatedAtUtc);
        Assert.Collection(
            metadata.SourceReports,
            source =>
            {
                Assert.Equal("v1_training", source.Name);
                Assert.Equal("board", source.Type);
                Assert.Equal(0, source.PreparedItemsCount);
            },
            source =>
            {
                Assert.Equal("mnist_train", source.Name);
                Assert.Equal("digit", source.Type);
                Assert.Equal(0, source.PreparedItemsCount);
            });
    }

    [Fact]
    public async Task Handle_ThrowsNotFound_WhenSelectedSourceDoesNotExist()
    {
        var handler = CreateHandler(
            sender: new StubSender(new ListRawDatasetCandidatesQueryResultDto(
                Items: [new ListRawDatasetCandidateItemDto("mnist_train", "digit")])));

        await Assert.ThrowsAsync<RawDatasetNotFoundException>(() => handler.Handle(
            new CreateDatasetPreparationCommand(
                PreparationName: "preparation-001",
                Sources: [new CreateDatasetPreparationSourceDto("v1_training", "board")]),
            CancellationToken.None));
    }

    [Fact]
    public async Task Handle_ThrowsConflict_WhenPreparationNameAlreadyExists()
    {
        var gateway = new InMemoryDatasetPreparationsGateway
        {
            ShouldCreateSucceed = false
        };
        var handler = CreateHandler(
            sender: new StubSender(new ListRawDatasetCandidatesQueryResultDto(
                Items: [new ListRawDatasetCandidateItemDto("v1_training", "board")])),
            gateway: gateway);

        await Assert.ThrowsAsync<FileStorageConflictException>(() => handler.Handle(
            new CreateDatasetPreparationCommand(
                PreparationName: "preparation-001",
                Sources: [new CreateDatasetPreparationSourceDto("v1_training", "board")]),
            CancellationToken.None));
    }

    private static CreateDatasetPreparationCommandHandler CreateHandler(
        ISender? sender = null,
        InMemoryDatasetPreparationsGateway? gateway = null,
        RecordingDatasetPreparationExecutionScheduler? scheduler = null)
    {
        return new CreateDatasetPreparationCommandHandler(
            sender ?? new StubSender(new ListRawDatasetCandidatesQueryResultDto(Items: [])),
            gateway ?? new InMemoryDatasetPreparationsGateway(),
            scheduler ?? new RecordingDatasetPreparationExecutionScheduler(),
            new FixedTimeProvider(FixedNow));
    }

    private sealed class InMemoryDatasetPreparationsGateway : IDatasetPreparationsGateway
    {
        public Dictionary<string, DatasetPreparationMetadataDto> Items { get; } = new(StringComparer.Ordinal);

        public bool ShouldCreateSucceed { get; init; } = true;

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
            if (!ShouldCreateSucceed)
            {
                return Task.FromResult(false);
            }

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
            Items.Remove(preparationName);
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

    private sealed class StubSender : ISender
    {
        private readonly object _response;

        public StubSender(object response)
        {
            _response = response;
        }

        public Task<TResponse> Send<TResponse>(
            IRequest<TResponse> request,
            CancellationToken cancellationToken = default)
        {
            return Task.FromResult((TResponse)_response);
        }

        public Task Send<TRequest>(TRequest request, CancellationToken cancellationToken = default)
            where TRequest : IRequest
        {
            throw new NotSupportedException();
        }

        public IAsyncEnumerable<TResponse> CreateStream<TResponse>(
            IStreamRequest<TResponse> request,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public IAsyncEnumerable<object?> CreateStream(
            object request,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task<object?> Send(object request, CancellationToken cancellationToken = default)
        {
            return Task.FromResult<object?>(_response);
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
