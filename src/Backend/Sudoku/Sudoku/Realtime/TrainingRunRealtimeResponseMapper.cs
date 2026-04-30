using Sudoku.Application.Trainings;
using Sudoku.Contracts;

namespace Sudoku.Realtime;

public static class TrainingRunRealtimeResponseMapper
{
    public const string SnapshotMessageKind = "snapshot";
    public const string EventMessageKind = "event";

    public static TrainingRunRealtimeApiResponse ToApiResponse(
        TrainingRunRealtimeSnapshotDto snapshot,
        string messageKind)
    {
        return new TrainingRunRealtimeApiResponse(
            MessageKind: messageKind,
            RunName: snapshot.RunName,
            Status: snapshot.Status,
            CreatedAtUtc: snapshot.CreatedAtUtc,
            UpdatedAtUtc: snapshot.UpdatedAtUtc,
            StartedAtUtc: snapshot.StartedAtUtc,
            FinishedAtUtc: snapshot.FinishedAtUtc,
            BaseModelName: snapshot.BaseModelName,
            ProducedModelName: snapshot.ProducedModelName,
            ProcessedDatasetName: snapshot.ProcessedDatasetName,
            TrainingMode: snapshot.TrainingMode,
            TrainingProfileName: snapshot.TrainingProfileName,
            AugmentationProfileName: snapshot.AugmentationProfileName,
            BenchmarkName: snapshot.BenchmarkName,
            Seed: snapshot.Seed,
            LastAcceptedSequence: snapshot.LastAcceptedSequence,
            LastEventType: snapshot.LastEventType,
            Progress: ToProgressApiResponse(snapshot.Progress),
            MetricsSummary: ToMetricsSummaryApiResponse(snapshot.MetricsSummary),
            ReportStatus: snapshot.ReportStatus,
            ReportRelativePath: snapshot.ReportRelativePath,
            Warnings: snapshot.Warnings,
            CleanupWarnings: snapshot.CleanupWarnings,
            FailureReason: snapshot.FailureReason);
    }

    public static TrainingRunRealtimeApiResponse ToApiResponse(
        TrainingRunMetadataDto metadata,
        string messageKind)
    {
        return ToApiResponse(ToSnapshot(metadata), messageKind);
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
            Progress: metadata.Progress,
            MetricsSummary: metadata.MetricsSummary,
            ReportStatus: metadata.ReportStatus,
            ReportRelativePath: metadata.ReportRelativePath,
            Warnings: metadata.Warnings ?? Array.Empty<string>(),
            CleanupWarnings: metadata.CleanupWarnings ?? Array.Empty<string>(),
            FailureReason: metadata.FailureReason);
    }

    private static TrainingRunProgressApiResponse? ToProgressApiResponse(TrainingRunProgressDto? progress)
    {
        return progress is null
            ? null
            : new TrainingRunProgressApiResponse(
                Percent: progress.Percent,
                Epoch: progress.Epoch,
                TotalEpochs: progress.TotalEpochs,
                TrainLoss: progress.TrainLoss,
                ValidationLoss: progress.ValidationLoss,
                TrainAccuracy: progress.TrainAccuracy,
                ValidationAccuracy: progress.ValidationAccuracy);
    }

    private static TrainingMetricsSummaryApiResponse? ToMetricsSummaryApiResponse(
        TrainingMetricsSummaryDto? metricsSummary)
    {
        return metricsSummary is null
            ? null
            : new TrainingMetricsSummaryApiResponse(
                Accuracy: metricsSummary.Accuracy,
                MacroF1: metricsSummary.MacroF1);
    }
}
