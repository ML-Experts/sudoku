using Microsoft.AspNetCore.SignalR;
using Sudoku.Application.SudokuSolve;
using Sudoku.Hubs;
using Sudoku.Models.Sudoku;

namespace Sudoku.Realtime;

public sealed class SignalRSudokuSolveEventPublisher : ISudokuSolveEventPublisher
{
    private const string SolveSnapshotClientMethod = "solveSnapshot";
    private const string SolveProgressClientMethod = "solveProgress";

    private readonly IHubContext<SudokuSolveHub> _hubContext;
    private readonly ILogger<SignalRSudokuSolveEventPublisher> _logger;

    public SignalRSudokuSolveEventPublisher(
        IHubContext<SudokuSolveHub> hubContext,
        ILogger<SignalRSudokuSolveEventPublisher> logger)
    {
        _hubContext = hubContext;
        _logger = logger;
    }

    public async Task PublishAsync(
        SolveSessionProgressSnapshotDto snapshot,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var response = SudokuSolveRealtimeResponseMapper.ToProgressApiResponse(snapshot);
            var groupName = SudokuSolveHubGroups.ForSolveSession(snapshot.SolveSessionId);
            var clientMethod = ResolveClientMethod(response.EventType);

            await _hubContext.Clients
                .Group(groupName)
                .SendAsync(clientMethod, response, CancellationToken.None);

            if (SudokuSolveSessionStatus.IsTerminal(snapshot.Status))
            {
                _logger.LogInformation(
                    "Published terminal sudoku solve event for session {SolveSessionId} with sequence {Sequence}, status {Status} and eventType {EventType}.",
                    snapshot.SolveSessionId,
                    response.Sequence,
                    snapshot.Status,
                    response.EventType);
            }
            else
            {
                _logger.LogDebug(
                    "Published sudoku solve event for session {SolveSessionId} with sequence {Sequence}, status {Status} and eventType {EventType}.",
                    snapshot.SolveSessionId,
                    response.Sequence,
                    snapshot.Status,
                    response.EventType);
            }
        }
        catch (OperationCanceledException exception)
        {
            _logger.LogInformation(
                exception,
                "Realtime sudoku solve publish was cancelled for session {SolveSessionId} with sequence {Sequence}.",
                snapshot.SolveSessionId,
                snapshot.Sequence ?? 0L);
        }
        catch (Exception exception)
        {
            _logger.LogWarning(
                exception,
                "Realtime sudoku solve publish failed for session {SolveSessionId} with sequence {Sequence}.",
                snapshot.SolveSessionId,
                snapshot.Sequence ?? 0L);
        }
    }

    private static string ResolveClientMethod(string eventType)
    {
        return string.Equals(eventType, SudokuSolveEventType.Snapshot, StringComparison.Ordinal)
            ? SolveSnapshotClientMethod
            : SolveProgressClientMethod;
    }
}
