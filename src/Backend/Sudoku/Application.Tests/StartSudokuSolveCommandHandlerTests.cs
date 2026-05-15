using System.Text.Json;
using Sudoku.Application.SudokuSolve;
using Sudoku.Models.Sudoku;

namespace Application.Tests;

public sealed class StartSudokuSolveCommandHandlerTests
{
    private static readonly DateTimeOffset FixedNow = DateTimeOffset.Parse("2026-05-15T18:30:00Z");

    [Fact]
    public async Task Handle_CreatesQueuedSessionAndSchedulesBackgroundWork_WhenGridIsValid()
    {
        var gateway = new InMemorySolveSessionsGateway();
        var scheduler = new StubSolveExecutionScheduler();
        var handler = CreateHandler(gateway, scheduler, solveSessionId: "solve-test-01");

        var result = await handler.Handle(
            new StartSudokuSolveCommand(ToJsonElement(CreateValidGrid())),
            CancellationToken.None);

        Assert.Equal("solve-test-01", result.SolveSessionId);
        Assert.Equal(SudokuSolveSessionStatus.Queued, result.Status);
        Assert.Equal("/ws/sudoku/solving/solve-test-01", result.ProgressChannelUrl);

        var metadata = Assert.Single(gateway.Items.Values);
        Assert.Equal("solve-test-01", metadata.SolveSessionId);
        Assert.Equal(SudokuSolveSessionStatus.Queued, metadata.Status);
        Assert.Equal(FixedNow, metadata.CreatedAtUtc);
        Assert.Equal("solve-test-01", Assert.Single(scheduler.ScheduledItems).SolveSessionId);
    }

    [Fact]
    public async Task Handle_ThrowsActiveSolveSessionAlreadyExistsException_WhenActiveSessionExists()
    {
        var gateway = new InMemorySolveSessionsGateway();
        gateway.Items["solve-existing"] = CreateMetadata(
            "solve-existing",
            SudokuSolveSessionStatus.Running);
        var handler = CreateHandler(gateway, new StubSolveExecutionScheduler(), solveSessionId: "solve-test-01");

        var exception = await Assert.ThrowsAsync<ActiveSolveSessionAlreadyExistsException>(() => handler.Handle(
            new StartSudokuSolveCommand(ToJsonElement(CreateValidGrid())),
            CancellationToken.None));

        Assert.Equal("solve-existing", exception.ActiveSolveSessionId);
    }

    [Fact]
    public async Task Handle_ThrowsSudokuGridConflictsException_WhenGridViolatesSudokuRules()
    {
        var gateway = new InMemorySolveSessionsGateway();
        var handler = CreateHandler(gateway, new StubSolveExecutionScheduler(), solveSessionId: "solve-test-01");

        var conflictingGrid = CreateValidGrid();
        conflictingGrid[0][1] = 5;

        await Assert.ThrowsAsync<SudokuGridConflictsException>(() => handler.Handle(
            new StartSudokuSolveCommand(ToJsonElement(conflictingGrid)),
            CancellationToken.None));
    }

    [Fact]
    public async Task Handle_RollsBackReservation_WhenSchedulingFails()
    {
        var gateway = new InMemorySolveSessionsGateway();
        var scheduler = new StubSolveExecutionScheduler
        {
            ThrowOnSchedule = true
        };
        var handler = CreateHandler(gateway, scheduler, solveSessionId: "solve-test-01");

        var exception = await Assert.ThrowsAsync<SolveSessionStartException>(() => handler.Handle(
            new StartSudokuSolveCommand(ToJsonElement(CreateValidGrid())),
            CancellationToken.None));

        Assert.Equal(SolveSudokuErrorTypes.SolveSessionEnqueueFailed, exception.ErrorType);
        Assert.Empty(gateway.Items);
    }

    private static StartSudokuSolveCommandHandler CreateHandler(
        InMemorySolveSessionsGateway gateway,
        StubSolveExecutionScheduler scheduler,
        string solveSessionId)
    {
        return new StartSudokuSolveCommandHandler(
            gateway,
            scheduler,
            new StubSolveSessionIdGenerator(solveSessionId),
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
        return new int?[][]
        {
            new int?[] { 5, 3, null, null, 7, null, null, null, null },
            new int?[] { 6, null, null, 1, 9, 5, null, null, null },
            new int?[] { null, 9, 8, null, null, null, null, 6, null },
            new int?[] { 8, null, null, null, 6, null, null, null, 3 },
            new int?[] { 4, null, null, 8, null, 3, null, null, 1 },
            new int?[] { 7, null, null, null, 2, null, null, null, 6 },
            new int?[] { null, 6, null, null, null, null, 2, 8, null },
            new int?[] { null, null, null, 4, 1, 9, null, null, 5 },
            new int?[] { null, null, null, null, 8, null, null, 7, 9 }
        };
    }

    private static JsonElement ToJsonElement<T>(T value)
    {
        return JsonSerializer.SerializeToElement(value);
    }

    private sealed class InMemorySolveSessionsGateway : ISolveSessionsGateway
    {
        public Dictionary<string, SolveSessionMetadataDto> Items { get; } = new(StringComparer.Ordinal);

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

    private sealed class StubSolveExecutionScheduler : ISudokuSolveExecutionScheduler
    {
        public bool ThrowOnSchedule { get; init; }

        public List<SolveSessionWorkItemDto> ScheduledItems { get; } = new();

        public Task ScheduleAsync(
            SolveSessionWorkItemDto workItem,
            CancellationToken cancellationToken = default)
        {
            if (ThrowOnSchedule)
            {
                throw new InvalidOperationException("scheduler failed");
            }

            ScheduledItems.Add(workItem);
            return Task.CompletedTask;
        }
    }

    private sealed class StubSolveSessionIdGenerator : ISolveSessionIdGenerator
    {
        private readonly string _solveSessionId;

        public StubSolveSessionIdGenerator(string solveSessionId)
        {
            _solveSessionId = solveSessionId;
        }

        public string Generate(DateTimeOffset createdAtUtc, int attempt)
        {
            return attempt == 0
                ? _solveSessionId
                : $"{_solveSessionId}-{attempt}";
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
