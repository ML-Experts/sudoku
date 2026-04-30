using System.Text.Json;
using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.SignalR;
using Sudoku.Application.Storage;
using Sudoku.Application.Trainings;
using Sudoku.Models.Trainings;
using Sudoku.Realtime;

namespace Sudoku.Hubs;

[Authorize]
public sealed class TrainingRunHub : Hub
{
    private const string TrainingSnapshotClientMethod = "trainingSnapshot";

    private readonly ISender _sender;
    private readonly ILogger<TrainingRunHub> _logger;

    public TrainingRunHub(
        ISender sender,
        ILogger<TrainingRunHub> logger)
    {
        _sender = sender;
        _logger = logger;
    }

    public override async Task OnConnectedAsync()
    {
        var runName = ResolveRunName();
        if (string.IsNullOrWhiteSpace(runName))
        {
            _logger.LogWarning("SignalR training connection without runName.");
            Context.Abort();
            return;
        }

        GetTrainingRunRealtimeSnapshotResultDto result;
        try
        {
            result = await _sender.Send(
                new GetTrainingRunRealtimeSnapshotQuery(runName),
                Context.ConnectionAborted);
        }
        catch (ValidationException exception)
        {
            _logger.LogWarning(
                exception,
                "SignalR training connection rejected for invalid runName.");
            Context.Abort();
            return;
        }
        catch (TrainingRunNotFoundForRealtimeException)
        {
            _logger.LogWarning(
                "SignalR training connection rejected for unknown run {RunName}.",
                runName);
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
                "Could not read realtime training snapshot for run {RunName}.",
                runName);
            Context.Abort();
            return;
        }

        var groupName = TrainingRunHubGroups.ForRun(result.Snapshot.RunName);
        await Groups.AddToGroupAsync(Context.ConnectionId, groupName, Context.ConnectionAborted);
        await Clients.Caller.SendAsync(
            TrainingSnapshotClientMethod,
            TrainingRunRealtimeResponseMapper.ToApiResponse(
                result.Snapshot,
                TrainingRunRealtimeResponseMapper.SnapshotMessageKind),
            Context.ConnectionAborted);

        if (TrainingRunStatus.IsTerminal(result.Snapshot.Status))
        {
            _logger.LogInformation(
                "Sent terminal training snapshot for run {RunName}.",
                result.Snapshot.RunName);
        }
        else
        {
            _logger.LogInformation(
                "Sent training snapshot for run {RunName}.",
                result.Snapshot.RunName);
        }

        await base.OnConnectedAsync();
    }

    private string? ResolveRunName()
    {
        var rawRunName = Context.GetHttpContext()?.Request.RouteValues["runName"]?.ToString();
        return string.IsNullOrWhiteSpace(rawRunName)
            ? null
            : rawRunName.Trim();
    }
}
