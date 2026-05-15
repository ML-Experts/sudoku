using Sudoku.Application.SudokuSolve;
using Sudoku.Models.Sudoku;

namespace Application.Tests;

public sealed class GetSolveSessionRealtimeSnapshotQueryHandlerTests
{
    private static readonly DateTimeOffset FixedNow = DateTimeOffset.Parse("2026-05-15T18:30:00Z");

    [Fact]
    public async Task Handle_ReturnsNormalizedRealtimeSnapshot_WhenSessionExists()
    {
        var gateway = new StubSolveSessionsGateway(
            CreateMetadata(
                solveSessionId: "solve-test-01",
                status: SudokuSolveSessionStatus.Running,
                lastAcceptedSequence: null,
                lastEventType: null));
        var handler = new GetSolveSessionRealtimeSnapshotQueryHandler(gateway);

        var result = await handler.Handle(
            new GetSolveSessionRealtimeSnapshotQuery("solve-test-01"),
            CancellationToken.None);

        Assert.Equal("solve-test-01", result.Snapshot.SolveSessionId);
        Assert.Equal(SudokuSolveSessionStatus.Running, result.Snapshot.Status);
        Assert.Equal(0L, result.Snapshot.Sequence);
        Assert.Equal(SudokuSolveEventType.Snapshot, result.Snapshot.EventType);
        AssertGridEqual(CreateValidGrid(), result.Snapshot.CurrentGrid);
    }

    [Fact]
    public async Task Handle_ThrowsSolveSessionNotFoundForRealtimeException_WhenSessionDoesNotExist()
    {
        var handler = new GetSolveSessionRealtimeSnapshotQueryHandler(new StubSolveSessionsGateway());

        var exception = await Assert.ThrowsAsync<SolveSessionNotFoundForRealtimeException>(() => handler.Handle(
            new GetSolveSessionRealtimeSnapshotQuery("missing-session"),
            CancellationToken.None));

        Assert.Equal("missing-session", exception.SolveSessionId);
    }

    private static SolveSessionMetadataDto CreateMetadata(
        string solveSessionId,
        string status,
        long? lastAcceptedSequence,
        string? lastEventType)
    {
        return new SolveSessionMetadataDto(
            SolveSessionId: solveSessionId,
            Status: status,
            CreatedAtUtc: FixedNow,
            UpdatedAtUtc: FixedNow,
            ProgressChannelUrl: $"/ws/sudoku/solving/{solveSessionId}",
            InputGrid: CreateValidGrid(),
            CurrentGrid: CreateValidGrid(),
            LastAcceptedSequence: lastAcceptedSequence,
            LastEventType: lastEventType);
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

    private static void AssertGridEqual(int?[][] expected, int?[][] actual)
    {
        Assert.Equal(expected.Length, actual.Length);

        for (var row = 0; row < expected.Length; row++)
        {
            Assert.Equal(expected[row].Length, actual[row].Length);

            for (var column = 0; column < expected[row].Length; column++)
            {
                Assert.Equal(expected[row][column], actual[row][column]);
            }
        }
    }

    private sealed class StubSolveSessionsGateway : ISolveSessionsGateway
    {
        private readonly Dictionary<string, SolveSessionMetadataDto> _items = new(StringComparer.Ordinal);

        public StubSolveSessionsGateway(params SolveSessionMetadataDto[] items)
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
            throw new NotSupportedException();
        }

        public Task UpdateAsync(
            SolveSessionMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task DeleteAsync(
            string solveSessionId,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }
    }
}
