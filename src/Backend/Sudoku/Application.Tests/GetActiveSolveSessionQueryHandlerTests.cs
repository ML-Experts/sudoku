using Sudoku.Application.SudokuSolve;
using Sudoku.Models.Sudoku;

namespace Application.Tests;

public sealed class GetActiveSolveSessionQueryHandlerTests
{
    private static readonly DateTimeOffset FixedNow = DateTimeOffset.Parse("2026-05-15T18:30:00Z");

    [Fact]
    public async Task Handle_ReturnsNoActiveSession_WhenStorageIsEmpty()
    {
        var handler = CreateHandler();

        var result = await handler.Handle(new GetActiveSolveSessionQuery(), CancellationToken.None);

        Assert.False(result.HasActiveSession);
        Assert.Null(result.Session);
    }

    [Theory]
    [InlineData(SudokuSolveSessionStatus.Queued)]
    [InlineData(SudokuSolveSessionStatus.Running)]
    [InlineData(SudokuSolveSessionStatus.Cancelling)]
    public async Task Handle_ReturnsActiveSession_WhenExactlyOneActiveSessionExists(string status)
    {
        var handler = CreateHandler(CreateMetadata("solve-active", status));

        var result = await handler.Handle(new GetActiveSolveSessionQuery(), CancellationToken.None);

        Assert.True(result.HasActiveSession);
        Assert.NotNull(result.Session);
        Assert.Equal("solve-active", result.Session!.SolveSessionId);
        Assert.Equal(status, result.Session.Status);
        Assert.Equal("/ws/sudoku/solving/solve-active", result.Session.ProgressChannelUrl);
    }

    [Fact]
    public async Task Handle_ReturnsNoActiveSession_WhenOnlyTerminalSessionsExist()
    {
        var handler = CreateHandler(
            CreateMetadata("solve-completed", SudokuSolveSessionStatus.Completed),
            CreateMetadata("solve-failed", SudokuSolveSessionStatus.Failed),
            CreateMetadata("solve-cancelled", SudokuSolveSessionStatus.Cancelled));

        var result = await handler.Handle(new GetActiveSolveSessionQuery(), CancellationToken.None);

        Assert.False(result.HasActiveSession);
        Assert.Null(result.Session);
    }

    [Fact]
    public async Task Handle_ThrowsInvalidOperationException_WhenMoreThanOneActiveSessionExists()
    {
        var handler = CreateHandler(
            CreateMetadata("solve-01", SudokuSolveSessionStatus.Queued),
            CreateMetadata("solve-02", SudokuSolveSessionStatus.Running));

        await Assert.ThrowsAsync<InvalidOperationException>(() =>
            handler.Handle(new GetActiveSolveSessionQuery(), CancellationToken.None));
    }

    [Fact]
    public async Task Handle_ThrowsInvalidOperationException_WhenActiveSessionHasBlankProgressChannelUrl()
    {
        var handler = CreateHandler(CreateMetadata(
            solveSessionId: "solve-broken",
            status: SudokuSolveSessionStatus.Running,
            progressChannelUrl: " "));

        await Assert.ThrowsAsync<InvalidOperationException>(() =>
            handler.Handle(new GetActiveSolveSessionQuery(), CancellationToken.None));
    }

    private static GetActiveSolveSessionQueryHandler CreateHandler(params SolveSessionMetadataDto[] items)
    {
        return new GetActiveSolveSessionQueryHandler(new InMemorySolveSessionsGateway(items));
    }

    private static SolveSessionMetadataDto CreateMetadata(
        string solveSessionId,
        string status,
        string? progressChannelUrl = null)
    {
        return new SolveSessionMetadataDto(
            SolveSessionId: solveSessionId,
            Status: status,
            CreatedAtUtc: FixedNow,
            UpdatedAtUtc: FixedNow,
            ProgressChannelUrl: progressChannelUrl ?? $"/ws/sudoku/solving/{solveSessionId}",
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
}
