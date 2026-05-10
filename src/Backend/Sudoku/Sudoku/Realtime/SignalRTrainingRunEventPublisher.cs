using Microsoft.AspNetCore.SignalR;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Trainings;
using Sudoku.Hubs;
using Sudoku.Models.Trainings;

namespace Sudoku.Realtime;

public sealed class SignalRTrainingRunEventPublisher : ITrainingRunEventPublisher
{
    private const string TrainingEventClientMethod = "trainingEvent";

    private readonly IHubContext<TrainingRunHub> _hubContext;
    private readonly ILogger<SignalRTrainingRunEventPublisher> _logger;

    public SignalRTrainingRunEventPublisher(
        IHubContext<TrainingRunHub> hubContext,
        ILogger<SignalRTrainingRunEventPublisher> logger)
    {
        _hubContext = hubContext;
        _logger = logger;
    }

    public async Task PublishAsync(
        TrainingRunMetadataDto metadata,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var response = TrainingRunRealtimeResponseMapper.ToEventApiResponse(metadata);
            var groupName = TrainingRunHubGroups.ForRun(metadata.RunName);

            await _hubContext.Clients
                .Group(groupName)
                .SendAsync(TrainingEventClientMethod, response, CancellationToken.None);

            if (TrainingRunStatus.IsTerminal(metadata.Status))
            {
                _logger.LogInformation(
                    "Published terminal training event for run {RunName} with sequence {Sequence}.",
                    metadata.RunName,
                    metadata.LastAcceptedSequence);
            }
            else
            {
                _logger.LogDebug(
                    "Published training event for run {RunName} with sequence {Sequence}.",
                    metadata.RunName,
                    metadata.LastAcceptedSequence);
            }
        }
        catch (OperationCanceledException exception)
        {
            _logger.LogInformation(
                exception,
                "Realtime training publish was cancelled for run {RunName} with sequence {Sequence}.",
                metadata.RunName,
                metadata.LastAcceptedSequence);
        }
        catch (Exception exception)
        {
            _logger.LogWarning(
                exception,
                "Realtime training publish failed for run {RunName} with sequence {Sequence}.",
                metadata.RunName,
                metadata.LastAcceptedSequence);
        }
    }
}
