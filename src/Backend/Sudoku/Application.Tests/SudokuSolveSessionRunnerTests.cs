using Sudoku.Application.SudokuSolve;
using Sudoku.Models.Sudoku;

namespace Application.Tests;

public sealed class SudokuSolveSessionRunnerTests
{
    private static readonly DateTimeOffset FixedNow = DateTimeOffset.Parse("2026-05-15T18:30:00Z");

    [Fact]
    public async Task RunAsync_AssignsNewTerminalSequence_WhenSolverFailsWithoutProgressSteps()
    {
        var initialMetadata = CreateMetadata("solve-test-01");
        var gateway = new InMemorySolveSessionsGateway(initialMetadata);
        var publisher = new RecordingSudokuSolveEventPublisher();
        var runner = new SudokuSolveSessionRunner(
            gateway,
            new StubSudokuBacktrackingSolver(SudokuBacktrackingSolveResultDto.UnsolvableResult()),
            publisher,
            new NoOpSolveSessionLockProvider(),
            new FixedTimeProvider(FixedNow));

        await runner.RunAsync(new SolveSessionWorkItemDto("solve-test-01"), CancellationToken.None);

        var publishedSnapshots = publisher.PublishedSnapshots;
        Assert.Equal(2, publishedSnapshots.Count);

        var runningSnapshot = publishedSnapshots[0];
        Assert.Equal(SudokuSolveEventType.Snapshot, runningSnapshot.EventType);
        Assert.Null(runningSnapshot.Sequence);

        var failedSnapshot = publishedSnapshots[1];
        Assert.Equal(SudokuSolveSessionStatus.Failed, failedSnapshot.Status);
        Assert.Equal(SudokuSolveEventType.Failed, failedSnapshot.EventType);
        Assert.Equal(1L, failedSnapshot.Sequence);
        Assert.Equal(SolveSudokuErrorTypes.Unsolvable, failedSnapshot.FailureErrorType);
    }

    private static SolveSessionMetadataDto CreateMetadata(string solveSessionId)
    {
        return new SolveSessionMetadataDto(
            SolveSessionId: solveSessionId,
            Status: SudokuSolveSessionStatus.Queued,
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
        private readonly Dictionary<string, SolveSessionMetadataDto> _items = new(StringComparer.Ordinal);

        public InMemorySolveSessionsGateway(params SolveSessionMetadataDto[] items)
        {
            foreach (var item in items)
            {
                _items[item.SolveSessionId] = item;
            }
        }

        public Task<IReadOnlyList<SolveSessionMetadataDto>> ListAsync(CancellationToken cancellationToken = default)
        {
            return Task.FromResult<IReadOnlyList<SolveSessionMetadataDto>>(_items.Values.ToArray());
        }

        public Task<SolveSessionMetadataDto?> GetBySolveSessionIdAsync(
            string solveSessionId,
            CancellationToken cancellationToken = default)
        {
            _items.TryGetValue(solveSessionId, out var metadata);
            return Task.FromResult(metadata);
        }

        public Task<bool> TryCreateAsync(
            SolveSessionMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            var created = _items.TryAdd(metadata.SolveSessionId, metadata);
            return Task.FromResult(created);
        }

        public Task UpdateAsync(
            SolveSessionMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            _items[metadata.SolveSessionId] = metadata;
            return Task.CompletedTask;
        }

        public Task DeleteAsync(
            string solveSessionId,
            CancellationToken cancellationToken = default)
        {
            _items.Remove(solveSessionId);
            return Task.CompletedTask;
        }
    }

    private sealed class StubSudokuBacktrackingSolver : ISudokuBacktrackingSolver
    {
        private readonly SudokuBacktrackingSolveResultDto _result;

        public StubSudokuBacktrackingSolver(SudokuBacktrackingSolveResultDto result)
        {
            _result = result;
        }

        public Task<SudokuBacktrackingSolveResultDto> SolveAsync(
            SudokuGrid grid,
            Func<SudokuSolverStepDto, CancellationToken, Task> onStepAsync,
            CancellationToken cancellationToken = default)
        {
            return Task.FromResult(_result);
        }
    }

    private sealed class RecordingSudokuSolveEventPublisher : ISudokuSolveEventPublisher
    {
        public List<SolveSessionProgressSnapshotDto> PublishedSnapshots { get; } = new();

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
