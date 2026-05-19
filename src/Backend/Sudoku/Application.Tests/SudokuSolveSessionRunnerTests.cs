using Sudoku.Application.SudokuSolve;
using Sudoku.Models.Sudoku;
using System.Diagnostics;
using System.Threading;

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

    [Fact]
    public async Task RunAsync_FinalizesCancelled_WhenTokenIsCancelledBeforeExecution()
    {
        using var cancellationTokenSource = new CancellationTokenSource();
        cancellationTokenSource.Cancel();

        var initialMetadata = CreateMetadata("solve-test-02");
        var gateway = new InMemorySolveSessionsGateway(initialMetadata);
        var publisher = new RecordingSudokuSolveEventPublisher();
        var runner = new SudokuSolveSessionRunner(
            gateway,
            new StubSudokuBacktrackingSolver(SudokuBacktrackingSolveResultDto.CompletedResult()),
            publisher,
            new NoOpSolveSessionLockProvider(),
            new FixedTimeProvider(FixedNow));

        await runner.RunAsync(new SolveSessionWorkItemDto("solve-test-02"), cancellationTokenSource.Token);

        var snapshot = Assert.Single(publisher.PublishedSnapshots);
        Assert.Equal(SudokuSolveSessionStatus.Cancelled, snapshot.Status);
        Assert.Equal(SudokuSolveEventType.Cancelled, snapshot.EventType);
        Assert.Equal(1L, snapshot.Sequence);
    }

    [Fact]
    public async Task RunAsync_FinalizesCancelled_WhenSessionIsAlreadyCancellingBeforeExecution()
    {
        var initialMetadata = CreateMetadata("solve-test-03") with
        {
            Status = SudokuSolveSessionStatus.Cancelling
        };
        var gateway = new InMemorySolveSessionsGateway(initialMetadata);
        var publisher = new RecordingSudokuSolveEventPublisher();
        var runner = new SudokuSolveSessionRunner(
            gateway,
            new StubSudokuBacktrackingSolver(SudokuBacktrackingSolveResultDto.CompletedResult()),
            publisher,
            new NoOpSolveSessionLockProvider(),
            new FixedTimeProvider(FixedNow));

        await runner.RunAsync(new SolveSessionWorkItemDto("solve-test-03"), CancellationToken.None);

        var snapshot = Assert.Single(publisher.PublishedSnapshots);
        Assert.Equal(SudokuSolveSessionStatus.Cancelled, snapshot.Status);
        Assert.Equal(SudokuSolveEventType.Cancelled, snapshot.EventType);
        Assert.Equal(1L, snapshot.Sequence);
    }

    [Fact]
    public async Task RunAsync_FinalizesCancelled_WhenSolverReturnsCancelled()
    {
        var initialMetadata = CreateMetadata("solve-test-04");
        var gateway = new InMemorySolveSessionsGateway(initialMetadata);
        var publisher = new RecordingSudokuSolveEventPublisher();
        var runner = new SudokuSolveSessionRunner(
            gateway,
            new StubSudokuBacktrackingSolver(SudokuBacktrackingSolveResultDto.CancelledResult()),
            publisher,
            new NoOpSolveSessionLockProvider(),
            new FixedTimeProvider(FixedNow));

        await runner.RunAsync(new SolveSessionWorkItemDto("solve-test-04"), CancellationToken.None);

        Assert.Equal(2, publisher.PublishedSnapshots.Count);
        Assert.Equal(SudokuSolveSessionStatus.Running, publisher.PublishedSnapshots[0].Status);
        Assert.Equal(SudokuSolveSessionStatus.Cancelled, publisher.PublishedSnapshots[1].Status);
        Assert.Equal(SudokuSolveEventType.Cancelled, publisher.PublishedSnapshots[1].EventType);
        Assert.Equal(1L, publisher.PublishedSnapshots[1].Sequence);
    }

    [Fact]
    public async Task RunAsync_AppliesDelayOnlyBetweenProgressSteps_WhenConfigured()
    {
        var initialMetadata = CreateMetadata(
            "solve-test-05",
            solverStepDelayMs: 50);
        var gateway = new InMemorySolveSessionsGateway(initialMetadata);
        var publisher = new RecordingSudokuSolveEventPublisher();
        var solver = new StepSequenceSudokuBacktrackingSolver(
            CreateProgressStep(CreateGridWithValue(0, 2, 4)),
            CreateProgressStep(CreateGridWithValue(0, 2, 4, 0, 3, 6)));
        var runner = new SudokuSolveSessionRunner(
            gateway,
            solver,
            publisher,
            new NoOpSolveSessionLockProvider(),
            new FixedTimeProvider(FixedNow));

        await runner.RunAsync(new SolveSessionWorkItemDto("solve-test-05"), CancellationToken.None);

        Assert.Equal(2, solver.StepDurations.Count);
        Assert.True(solver.StepDurations[0] < TimeSpan.FromMilliseconds(40));
        Assert.True(solver.StepDurations[1] >= TimeSpan.FromMilliseconds(40));

        Assert.Equal(4, publisher.PublishedSnapshots.Count);
        Assert.Equal(SudokuSolveEventType.Snapshot, publisher.PublishedSnapshots[0].EventType);
        Assert.Equal(SudokuSolveEventType.Progress, publisher.PublishedSnapshots[1].EventType);
        Assert.Equal(SudokuSolveEventType.Progress, publisher.PublishedSnapshots[2].EventType);
        Assert.Equal(SudokuSolveEventType.Completed, publisher.PublishedSnapshots[3].EventType);
    }

    [Fact]
    public async Task RunAsync_DoesNotDelayProgressSteps_WhenConfiguredDelayIsZero()
    {
        var initialMetadata = CreateMetadata(
            "solve-test-06",
            solverStepDelayMs: 0);
        var gateway = new InMemorySolveSessionsGateway(initialMetadata);
        var publisher = new RecordingSudokuSolveEventPublisher();
        var solver = new StepSequenceSudokuBacktrackingSolver(
            CreateProgressStep(CreateGridWithValue(0, 2, 4)),
            CreateProgressStep(CreateGridWithValue(0, 2, 4, 0, 3, 6)));
        var runner = new SudokuSolveSessionRunner(
            gateway,
            solver,
            publisher,
            new NoOpSolveSessionLockProvider(),
            new FixedTimeProvider(FixedNow));

        await runner.RunAsync(new SolveSessionWorkItemDto("solve-test-06"), CancellationToken.None);

        Assert.Equal(2, solver.StepDurations.Count);
        Assert.True(solver.StepDurations[0] < TimeSpan.FromMilliseconds(40));
        Assert.True(solver.StepDurations[1] < TimeSpan.FromMilliseconds(40));
    }

    [Fact]
    public async Task RunAsync_DoesNotDelayLegacySession_WhenEffectiveParametersAreMissing()
    {
        var initialMetadata = CreateMetadata("solve-test-07");
        var gateway = new InMemorySolveSessionsGateway(initialMetadata);
        var publisher = new RecordingSudokuSolveEventPublisher();
        var solver = new StepSequenceSudokuBacktrackingSolver(
            CreateProgressStep(CreateGridWithValue(0, 2, 4)),
            CreateProgressStep(CreateGridWithValue(0, 2, 4, 0, 3, 6)));
        var runner = new SudokuSolveSessionRunner(
            gateway,
            solver,
            publisher,
            new NoOpSolveSessionLockProvider(),
            new FixedTimeProvider(FixedNow));

        await runner.RunAsync(new SolveSessionWorkItemDto("solve-test-07"), CancellationToken.None);

        Assert.Equal(2, solver.StepDurations.Count);
        Assert.True(solver.StepDurations[0] < TimeSpan.FromMilliseconds(40));
        Assert.True(solver.StepDurations[1] < TimeSpan.FromMilliseconds(40));
    }

    [Fact]
    public async Task RunAsync_FinalizesCancelled_WhenCancellationHappensDuringInterStepDelay()
    {
        using var cancellationTokenSource = new CancellationTokenSource();

        var initialMetadata = CreateMetadata(
            "solve-test-08",
            solverStepDelayMs: 200);
        var gateway = new InMemorySolveSessionsGateway(initialMetadata);
        var publisher = new RecordingSudokuSolveEventPublisher();
        var solver = new StepSequenceSudokuBacktrackingSolver(
            CreateProgressStep(CreateGridWithValue(0, 2, 4)),
            CreateProgressStep(CreateGridWithValue(0, 2, 4, 0, 3, 6)));
        var runner = new SudokuSolveSessionRunner(
            gateway,
            solver,
            publisher,
            new NoOpSolveSessionLockProvider(),
            new FixedTimeProvider(FixedNow));

        var runTask = runner.RunAsync(
            new SolveSessionWorkItemDto("solve-test-08"),
            cancellationTokenSource.Token);

        await publisher.WaitForCountAsync(2, CancellationToken.None);
        cancellationTokenSource.Cancel();
        await runTask;

        Assert.Equal(3, publisher.PublishedSnapshots.Count);
        Assert.Equal(SudokuSolveEventType.Progress, publisher.PublishedSnapshots[1].EventType);
        Assert.Equal(SudokuSolveSessionStatus.Cancelled, publisher.PublishedSnapshots[2].Status);
        Assert.Equal(SudokuSolveEventType.Cancelled, publisher.PublishedSnapshots[2].EventType);
    }

    private static SolveSessionMetadataDto CreateMetadata(
        string solveSessionId,
        int? solverStepDelayMs = null)
    {
        return new SolveSessionMetadataDto(
            SolveSessionId: solveSessionId,
            Status: SudokuSolveSessionStatus.Queued,
            CreatedAtUtc: FixedNow,
            UpdatedAtUtc: FixedNow,
            ProgressChannelUrl: $"/ws/sudoku/solving/{solveSessionId}",
            InputGrid: CreateValidGrid(),
            CurrentGrid: CreateValidGrid(),
            EffectiveParameters: solverStepDelayMs is null
                ? null
                : new SudokuSolveEffectiveParametersDto(solverStepDelayMs.Value));
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

    private static int?[][] CreateGridWithValue(params int[] entries)
    {
        var grid = CreateValidGrid();
        for (var index = 0; index < entries.Length; index += 3)
        {
            grid[entries[index]][entries[index + 1]] = entries[index + 2];
        }

        return grid;
    }

    private static SudokuSolverStepDto CreateProgressStep(int?[][] currentGrid)
    {
        return new SudokuSolverStepDto(
            EventType: SudokuSolveEventType.Progress,
            CurrentGrid: currentGrid,
            Position: new SudokuCellPosition(0, 0),
            Digit: currentGrid[0][0]);
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

    private sealed class StepSequenceSudokuBacktrackingSolver : ISudokuBacktrackingSolver
    {
        private readonly IReadOnlyList<SudokuSolverStepDto> _steps;

        public StepSequenceSudokuBacktrackingSolver(params SudokuSolverStepDto[] steps)
        {
            _steps = steps;
        }

        public List<TimeSpan> StepDurations { get; } = new();

        public async Task<SudokuBacktrackingSolveResultDto> SolveAsync(
            SudokuGrid grid,
            Func<SudokuSolverStepDto, CancellationToken, Task> onStepAsync,
            CancellationToken cancellationToken = default)
        {
            foreach (var step in _steps)
            {
                var stopwatch = Stopwatch.StartNew();
                await onStepAsync(step, cancellationToken);
                stopwatch.Stop();
                StepDurations.Add(stopwatch.Elapsed);
            }

            return SudokuBacktrackingSolveResultDto.CompletedResult();
        }
    }

    private sealed class RecordingSudokuSolveEventPublisher : ISudokuSolveEventPublisher
    {
        private readonly SemaphoreSlim _signal = new(0);
        private readonly List<SolveSessionProgressSnapshotDto> _publishedSnapshots = new();

        public IReadOnlyList<SolveSessionProgressSnapshotDto> PublishedSnapshots
        {
            get
            {
                lock (_publishedSnapshots)
                {
                    return _publishedSnapshots.ToArray();
                }
            }
        }

        public Task PublishAsync(
            SolveSessionProgressSnapshotDto snapshot,
            CancellationToken cancellationToken = default)
        {
            lock (_publishedSnapshots)
            {
                _publishedSnapshots.Add(snapshot);
            }

            _signal.Release();
            return Task.CompletedTask;
        }

        public async Task WaitForCountAsync(int expectedCount, CancellationToken cancellationToken)
        {
            while (true)
            {
                lock (_publishedSnapshots)
                {
                    if (_publishedSnapshots.Count >= expectedCount)
                    {
                        return;
                    }
                }

                await _signal.WaitAsync(cancellationToken);
            }
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
