using MediatR;
using Sudoku.Application.Abstractions;

namespace Sudoku.Application.Trainings;

public sealed class GetTrainingRunRealtimeSnapshotQueryHandler
    : IRequestHandler<GetTrainingRunRealtimeSnapshotQuery, GetTrainingRunRealtimeSnapshotResultDto>
{
    private readonly ITrainingRunsGateway _trainingRunsGateway;

    public GetTrainingRunRealtimeSnapshotQueryHandler(ITrainingRunsGateway trainingRunsGateway)
    {
        _trainingRunsGateway = trainingRunsGateway;
    }

    public async Task<GetTrainingRunRealtimeSnapshotResultDto> Handle(
        GetTrainingRunRealtimeSnapshotQuery request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.RunName))
        {
            throw new InvalidOperationException("GetTrainingRunRealtimeSnapshotQuery must be validated before handler execution.");
        }

        var runName = request.RunName.Trim();
        var metadata = await _trainingRunsGateway.GetByRunNameAsync(runName, cancellationToken);
        if (metadata is null)
        {
            throw new TrainingRunNotFoundForRealtimeException(runName);
        }

        return new GetTrainingRunRealtimeSnapshotResultDto(ToSnapshot(metadata));
    }

    private static TrainingRunRealtimeSnapshotDto ToSnapshot(TrainingRunMetadataDto metadata)
    {
        return new TrainingRunRealtimeSnapshotDto(
            RunName: metadata.RunName,
            Status: metadata.Status,
            CreatedAtUtc: metadata.CreatedAtUtc,
            UpdatedAtUtc: metadata.UpdatedAtUtc,
            StartedAtUtc: metadata.StartedAtUtc,
            FinishedAtUtc: metadata.FinishedAtUtc,
            BaseModelName: metadata.BaseModelName,
            ProducedModelName: metadata.ProducedModelName,
            ProcessedDatasetName: metadata.ProcessedDatasetName,
            TrainingMode: metadata.TrainingMode,
            TrainingProfileName: metadata.TrainingProfileName,
            AugmentationProfileName: metadata.AugmentationProfileName,
            BenchmarkName: metadata.BenchmarkName,
            Seed: metadata.Seed,
            LastAcceptedSequence: metadata.LastAcceptedSequence,
            LastEventType: metadata.LastEventType,
            Stage: metadata.Stage,
            LastEventMessage: metadata.LastEventMessage,
            LastEventOccurredAtUtc: metadata.LastEventOccurredAtUtc,
            Progress: metadata.Progress,
            MetricsSummary: metadata.MetricsSummary,
            ReportStatus: metadata.ReportStatus,
            ReportRelativePath: metadata.ReportRelativePath,
            PrimaryArtifactRelativePath: metadata.PrimaryArtifactRelativePath,
            ReportArtifacts: metadata.ReportArtifacts,
            Warnings: metadata.Warnings ?? Array.Empty<string>(),
            CleanupWarnings: metadata.CleanupWarnings ?? Array.Empty<string>(),
            FailureReason: metadata.FailureReason,
            FailureErrorType: metadata.FailureErrorType);
    }
}
