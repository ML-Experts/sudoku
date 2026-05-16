using Sudoku.Application.Abstractions;
using Sudoku.Application.SudokuSolve;
using Sudoku.Models.Sudoku;

namespace Application.Tests;

public sealed class CancelSolveSessionCommandHandlerTests
{
    private static readonly DateTimeOffset FixedNow = DateTimeOffset.Parse("2026-05-16T10:15:00Z");

    [Fact]
    public async Task Handle_ReturnsNotFound_WhenSessionDoesNotExist()
    {
        var handler = CreateHandler(
            new InMemorySolveSessionsGateway(),
            new TestBackgroundOperationCancellationRegistry(),
            new RecordingSudokuSolveEventPublisher());

        var result = await handler.Handle(new CancelSolveSessionCommand("solve-missing"), CancellationToken.None);

        Assert.Null(result.Status);
        Assert.Equal(CancelSolveSessionDispositions.NotFound, result.RequestDisposition);
    }

    [Fact]
    public async Task Handle_ReturnsAcceptedAndCancelling_WhenQueuedSessionHasLiveExecution()
    {
        var gateway = new InMemorySolveSessionsGateway(CreateMetadata("solve-live", SudokuSolveSessionStatus.Queued));
        var registry = new TestBackgroundOperationCancellationRegistry();
        registry.Register("solve-live");
        var publisher = new RecordingSudokuSolveEventPublisher();
        var handler = CreateHandler(gateway, registry, publisher);

        var result = await handler.Handle(new CancelSolveSessionCommand("solve-live"), CancellationToken.None);

        Assert.Equal(SudokuSolveSessionStatus.Cancelling, result.Status);
        Assert.Equal(CancelSolveSessionDispositions.Accepted, result.RequestDisposition);

        var updated = Assert.Single(gateway.Items.Values);
        Assert.Equal(SudokuSolveSessionStatus.Cancelling, updated.Status);
        Assert.True(registry.IsCancellationRequested("solve-live"));
        Assert.Empty(publisher.PublishedSnapshots);
    }

    [Fact]
    public async Task Handle_FinalizesCancelled_WhenRunningSessionHasNoLiveExecution()
    {
        var gateway = new InMemorySolveSessionsGateway(CreateMetadata("solve-stale", SudokuSolveSessionStatus.Running));
        var publisher = new RecordingSudokuSolveEventPublisher();
        var handler = CreateHandler(
            gateway,
            new TestBackgroundOperationCancellationRegistry(),
            publisher);

        var result = await handler.Handle(new CancelSolveSessionCommand("solve-stale"), CancellationToken.None);

        Assert.Equal(SudokuSolveSessionStatus.Cancelled, result.Status);
        Assert.Equal(CancelSolveSessionDispositions.Accepted, result.RequestDisposition);

        var updated = Assert.Single(gateway.Items.Values);
        Assert.Equal(SudokuSolveSessionStatus.Cancelled, updated.Status);
        Assert.Equal(1L, updated.LastAcceptedSequence);
        Assert.Equal(SudokuSolveEventType.Cancelled, updated.LastEventType);

        var snapshot = Assert.Single(publisher.PublishedSnapshots);
        Assert.Equal(SudokuSolveSessionStatus.Cancelled, snapshot.Status);
        Assert.Equal(SudokuSolveEventType.Cancelled, snapshot.EventType);
    }

    [Fact]
    public async Task Handle_ReturnsDuplicate_WhenSessionIsAlreadyCancellingAndHasLiveExecution()
    {
        var gateway = new InMemorySolveSessionsGateway(CreateMetadata("solve-cancelling", SudokuSolveSessionStatus.Cancelling));
        var registry = new TestBackgroundOperationCancellationRegistry();
        registry.Register("solve-cancelling");
        var handler = CreateHandler(
            gateway,
            registry,
            new RecordingSudokuSolveEventPublisher());

        var result = await handler.Handle(new CancelSolveSessionCommand("solve-cancelling"), CancellationToken.None);

        Assert.Equal(SudokuSolveSessionStatus.Cancelling, result.Status);
        Assert.Equal(CancelSolveSessionDispositions.Duplicate, result.RequestDisposition);
    }

    [Fact]
    public async Task Handle_ReturnsAlreadyFinished_WhenSessionIsTerminal()
    {
        var gateway = new InMemorySolveSessionsGateway(CreateMetadata("solve-completed", SudokuSolveSessionStatus.Completed));
        var handler = CreateHandler(
            gateway,
            new TestBackgroundOperationCancellationRegistry(),
            new RecordingSudokuSolveEventPublisher());

        var result = await handler.Handle(new CancelSolveSessionCommand("solve-completed"), CancellationToken.None);

        Assert.Equal(SudokuSolveSessionStatus.Completed, result.Status);
        Assert.Equal(CancelSolveSessionDispositions.AlreadyFinished, result.RequestDisposition);
    }

    [Fact]
    public async Task Handle_ThrowsInvalidOperationException_WhenMultipleActiveSessionsExist()
    {
        var gateway = new InMemorySolveSessionsGateway(
            CreateMetadata("solve-first", SudokuSolveSessionStatus.Running),
            CreateMetadata("solve-second", SudokuSolveSessionStatus.Queued));
        var handler = CreateHandler(
            gateway,
            new TestBackgroundOperationCancellationRegistry(),
            new RecordingSudokuSolveEventPublisher());

        await Assert.ThrowsAsync<InvalidOperationException>(() => handler.Handle(
            new CancelSolveSessionCommand("solve-first"),
            CancellationToken.None));
    }

    [Fact]
    public async Task Handle_ThrowsSolveSessionCancelPersistenceException_WhenMetadataUpdateFails()
    {
        var gateway = new InMemorySolveSessionsGateway(CreateMetadata("solve-failing", SudokuSolveSessionStatus.Queued))
        {
            ThrowOnUpdate = true
        };
        var registry = new TestBackgroundOperationCancellationRegistry();
        registry.Register("solve-failing");
        var handler = CreateHandler(
            gateway,
            registry,
            new RecordingSudokuSolveEventPublisher());

        await Assert.ThrowsAsync<SolveSessionCancelPersistenceException>(() => handler.Handle(
            new CancelSolveSessionCommand("solve-failing"),
            CancellationToken.None));
    }

    private static CancelSolveSessionCommandHandler CreateHandler(
        InMemorySolveSessionsGateway gateway,
        TestBackgroundOperationCancellationRegistry registry,
        RecordingSudokuSolveEventPublisher publisher)
    {
        return new CancelSolveSessionCommandHandler(
            gateway,
            registry,
            publisher,
            new NoOpSolveSessionLockProvider(),
            new FixedTimeProvider(FixedNow));
    }

    private static SolveSessionMetadataDto CreateMetadata(
        string solveSessionId,
        string status)
    {
        return new SolveSessionMetadataDto(
            SolveSessionId: solveSessionId,
            Status: status,
            CreatedAtUtc: FixedNow,
            UpdatedAtUtc: FixedNow,
            ProgressChannelUrl: $"/ws/sudoku/solving/{solveSessionId}",
            InputGrid: CreateValidGrid(),
            CurrentGrid: CreateValidGrid());
    }

    private static int?[][] CreateValidGrid()
    {
        return
        [
            [5, 3, null, null, 7, null, null, null, null],
            [6, null, null, 1, 9, 5, null, null, null],
            [null, 9, 8, null, null, null, null, 6, null],
            [8, null, null, null, 6, null, null, null, 3],
            [4, null, null, 8, null, 3, null, null, 1],
            [7, null, null, null, 2, null, null, null, 6],
            [null, 6, null, null, null, null, 2, 8, null],
            [null, null, null, 4, 1, 9, null, null, 5],
            [null, null, null, null, 8, null, null, 7, 9]
        ];
    }

    private sealed class InMemorySolveSessionsGateway : ISolveSessionsGateway
    {
        public Dictionary<string, SolveSessionMetadataDto> Items { get; } = new(StringComparer.Ordinal);

        public bool ThrowOnUpdate { get; init; }

        public InMemorySolveSessionsGateway(params SolveSessionMetadataDto[] items)
        {
            foreach (var item in items)
            {
                Items[item.SolveSessionId] = item;
            }
        }

        public Task<IReadOnlyList<SolveSessionMetadataDto>> ListAsync(CancellationToken cancellationToken = default)
        {
            return Task.FromResult<IReadOnlyList<SolveSessionMetadataDto>>(Items.Values.ToArray());
        }

        public Task<SolveSessionMetadataDto?> GetBySolveSessionIdAsync(
            string solveSessionId,
            CancellationToken cancellationToken = default)
        {
            Items.TryGetValue(solveSessionId, out var metadata);
            return Task.FromResult(metadata);
        }

        public Task<bool> TryCreateAsync(
            SolveSessionMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            var created = Items.TryAdd(metadata.SolveSessionId, metadata);
            return Task.FromResult(created);
        }

        public Task UpdateAsync(
            SolveSessionMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            if (ThrowOnUpdate)
            {
                throw new IOException("update failed");
            }

            Items[metadata.SolveSessionId] = metadata;
            return Task.CompletedTask;
        }

        public Task DeleteAsync(
            string solveSessionId,
            CancellationToken cancellationToken = default)
        {
            Items.Remove(solveSessionId);
            return Task.CompletedTask;
        }
    }

    private sealed class TestBackgroundOperationCancellationRegistry : IBackgroundOperationCancellationRegistry
    {
        private readonly Dictionary<string, CancellationTokenSource> _items = new(StringComparer.Ordinal);

        public CancellationToken Register(string operationId)
        {
            var cancellationTokenSource = new CancellationTokenSource();
            _items.Add(operationId, cancellationTokenSource);
            return cancellationTokenSource.Token;
        }

        public bool TryGetCancellationToken(string operationId, out CancellationToken cancellationToken)
        {
            if (_items.TryGetValue(operationId, out var cancellationTokenSource))
            {
                cancellationToken = cancellationTokenSource.Token;
                return true;
            }

            cancellationToken = CancellationToken.None;
            return false;
        }

        public bool TryCancel(string operationId)
        {
            if (!_items.TryGetValue(operationId, out var cancellationTokenSource))
            {
                return false;
            }

            cancellationTokenSource.Cancel();
            return true;
        }

        public void Complete(string operationId)
        {
            if (_items.Remove(operationId, out var cancellationTokenSource))
            {
                cancellationTokenSource.Dispose();
            }
        }

        public bool IsCancellationRequested(string operationId)
        {
            return _items.TryGetValue(operationId, out var cancellationTokenSource)
                   && cancellationTokenSource.IsCancellationRequested;
        }
    }

    private sealed class RecordingSudokuSolveEventPublisher : ISudokuSolveEventPublisher
    {
        public List<SolveSessionProgressSnapshotDto> PublishedSnapshots { get; } = [];

        public Task PublishAsync(
            SolveSessionProgressSnapshotDto snapshot,
            CancellationToken cancellationToken = default)
        {
            PublishedSnapshots.Add(snapshot);
            return Task.CompletedTask;
        }
    }

    private sealed class NoOpSolveSessionLockProvider : ISolveSessionLockProvider
    {
        public ValueTask<IAsyncDisposable> AcquireAsync(
            string solveSessionId,
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
