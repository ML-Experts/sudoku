using System.Text.Json;
using MediatR;
using Microsoft.AspNetCore.SignalR;
using Sudoku.Application.Storage;
using Sudoku.Application.SudokuSolve;
using Sudoku.Models.Sudoku;
using Sudoku.Realtime;

namespace Sudoku.Hubs;

public sealed class SudokuSolveHub : Hub
{
    private const string SolveSnapshotClientMethod = "solveSnapshot";

    private readonly ISender _sender;
    private readonly ILogger<SudokuSolveHub> _logger;

    public SudokuSolveHub(
        ISender sender,
        ILogger<SudokuSolveHub> logger)
    {
        _sender = sender;
        _logger = logger;
    }

    public override async Task OnConnectedAsync()
    {
        var solveSessionId = ResolveSolveSessionId();
        if (string.IsNullOrWhiteSpace(solveSessionId))
        {
            _logger.LogWarning("SignalR sudoku solve connection without solveSessionId.");
            Context.Abort();
            return;
        }

        GetSolveSessionRealtimeSnapshotResultDto result;
        try
        {
            result = await _sender.Send(
                new GetSolveSessionRealtimeSnapshotQuery(solveSessionId),
                Context.ConnectionAborted);
        }
        catch (SolveSessionNotFoundForRealtimeException)
        {
            _logger.LogWarning(
                "SignalR sudoku solve connection rejected for unknown solveSessionId {SolveSessionId}.",
                solveSessionId);
            Context.Abort();
            return;
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidDataException
                                         or JsonException
                                         or FileStorageItemNotFoundException)
        {
            _logger.LogError(
                exception,
                "Could not read realtime sudoku solve snapshot for session {SolveSessionId}.",
                solveSessionId);
            Context.Abort();
            return;
        }

        var groupName = SudokuSolveHubGroups.ForSolveSession(result.Snapshot.SolveSessionId);
        await Groups.AddToGroupAsync(Context.ConnectionId, groupName, Context.ConnectionAborted);
        await Clients.Caller.SendAsync(
            SolveSnapshotClientMethod,
            SudokuSolveRealtimeResponseMapper.ToSnapshotApiResponse(result.Snapshot),
            Context.ConnectionAborted);

        if (SudokuSolveSessionStatus.IsTerminal(result.Snapshot.Status))
        {
            _logger.LogInformation(
                "Sent terminal sudoku solve snapshot for session {SolveSessionId} with sequence {Sequence}.",
                result.Snapshot.SolveSessionId,
                result.Snapshot.Sequence);
        }
        else
        {
            _logger.LogInformation(
                "Sent sudoku solve snapshot for session {SolveSessionId} with sequence {Sequence}.",
                result.Snapshot.SolveSessionId,
                result.Snapshot.Sequence);
        }

        await base.OnConnectedAsync();
    }

    private string? ResolveSolveSessionId()
    {
        var rawSolveSessionId = Context.GetHttpContext()?.Request.RouteValues["solveSessionId"]?.ToString();
        return string.IsNullOrWhiteSpace(rawSolveSessionId)
            ? null
            : rawSolveSessionId.Trim();
    }
}
