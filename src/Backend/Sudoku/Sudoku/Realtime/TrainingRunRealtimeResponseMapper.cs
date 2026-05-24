using Sudoku.Application.Trainings;
using Sudoku.Contracts;
using Sudoku.Models.Trainings;

namespace Sudoku.Realtime;

public static class TrainingRunRealtimeResponseMapper
{
    private const string SnapshotEventType = "snapshot";
    private const string StatusChangedEventType = "statusChanged";
    private const string TrainingStage = "training";
    private const string QueuedStage = "queued";
    private const string EvaluationStage = "evaluation";
    private const string FinishedStage = "finished";
    private const string DefaultFailureErrorType = "training_run_failed";

    public static TrainingRunSocketEventApiResponse ToSnapshotApiResponse(
        TrainingRunRealtimeSnapshotDto snapshot)
    {
        return ToApiResponse(
            EventType: SnapshotEventType,
            Sequence: snapshot.LastAcceptedSequence ?? 0,
            RunName: snapshot.RunName,
            Status: snapshot.Status,
            Stage: ResolveStage(snapshot.Status, snapshot.Stage),
            OccurredAtUtc: snapshot.LastEventOccurredAtUtc
                           ?? snapshot.UpdatedAtUtc
                           ?? snapshot.CreatedAtUtc,
            Message: snapshot.LastEventMessage,
            Progress: snapshot.Progress,
            Warnings: MergeWarnings(snapshot.Warnings, snapshot.CleanupWarnings),
            Result: BuildResult(snapshot),
            Failure: BuildFailure(snapshot));
    }

    public static TrainingRunSocketEventApiResponse ToEventApiResponse(
        TrainingRunMetadataDto metadata)
    {
        var snapshot = ToSnapshot(metadata);
        return ToApiResponse(
            EventType: snapshot.LastEventType ?? StatusChangedEventType,
            Sequence: snapshot.LastAcceptedSequence ?? 0,
            RunName: snapshot.RunName,
            Status: snapshot.Status,
            Stage: ResolveStage(snapshot.Status, snapshot.Stage),
            OccurredAtUtc: snapshot.LastEventOccurredAtUtc
                           ?? snapshot.UpdatedAtUtc
                           ?? snapshot.CreatedAtUtc,
            Message: snapshot.LastEventMessage,
            Progress: snapshot.Progress,
            Warnings: MergeWarnings(snapshot.Warnings, snapshot.CleanupWarnings),
            Result: BuildResult(snapshot),
            Failure: BuildFailure(snapshot));
    }

    private static TrainingRunSocketEventApiResponse ToApiResponse(
        string EventType,
        long Sequence,
        string RunName,
        string Status,
        string Stage,
        DateTimeOffset OccurredAtUtc,
        string? Message,
        TrainingRunProgressDto? Progress,
        IReadOnlyList<string> Warnings,
        TrainingRunResultApiResponse? Result,
        TrainingRunFailureApiResponse? Failure)
    {
        return new TrainingRunSocketEventApiResponse(
            EventType: EventType,
            Sequence: Sequence,
            RunName: RunName,
            Status: Status,
            Stage: Stage,
            OccurredAtUtc: OccurredAtUtc,
            Message: Message,
            Progress: ToProgressApiResponse(Progress),
            Warnings: Warnings,
            Result: Result,
            Failure: Failure);
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

    private static TrainingRunProgressApiResponse? ToProgressApiResponse(TrainingRunProgressDto? progress)
    {
        return progress is null
            ? null
            : new TrainingRunProgressApiResponse(
                Percent: progress.Percent,
                EpochCurrent: progress.Epoch,
                EpochTotal: progress.TotalEpochs,
                TrainLoss: progress.TrainLoss,
                ValidationLoss: progress.ValidationLoss,
                TrainAccuracy: progress.TrainAccuracy,
                ValidationAccuracy: progress.ValidationAccuracy,
                EtaSeconds: progress.EtaSeconds);
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

    private static TrainingRunResultApiResponse? BuildResult(TrainingRunRealtimeSnapshotDto snapshot)
    {
        if (!TrainingRunStatus.IsTerminal(snapshot.Status)
            || !string.Equals(snapshot.Status, TrainingRunStatus.Succeeded, StringComparison.Ordinal))
        {
            return null;
        }

        return new TrainingRunResultApiResponse(
            ProducedModelName: snapshot.ProducedModelName,
            ReportStatus: snapshot.ReportStatus ?? "missing",
            CanUseProducedModelForInference: true,
            PrimaryArtifactRelativePath: snapshot.PrimaryArtifactRelativePath ?? string.Empty,
            SummaryRelativePath: snapshot.ReportArtifacts?.SummaryRelativePath,
            MetricsRelativePath: snapshot.ReportArtifacts?.MetricsRelativePath,
            ConfusionMatrixRelativePath: snapshot.ReportArtifacts?.ConfusionMatrixRelativePath,
            MetricsSummary: ToMetricsSummaryApiResponse(snapshot.MetricsSummary));
    }

    private static TrainingRunFailureApiResponse? BuildFailure(TrainingRunRealtimeSnapshotDto snapshot)
    {
        if (!string.Equals(snapshot.Status, TrainingRunStatus.Failed, StringComparison.Ordinal))
        {
            return null;
        }

        return new TrainingRunFailureApiResponse(
            ErrorType: string.IsNullOrWhiteSpace(snapshot.FailureErrorType)
                ? DefaultFailureErrorType
                : snapshot.FailureErrorType,
            Message: string.IsNullOrWhiteSpace(snapshot.FailureReason)
                ? "Run treningowy zakończył się błędem technicznym."
                : snapshot.FailureReason,
            CanUseProducedModelForInference: false);
    }

    private static string ResolveStage(string status, string? stage)
    {
        if (!string.IsNullOrWhiteSpace(stage))
        {
            return stage;
        }

        return status switch
        {
            TrainingRunStatus.Queued or TrainingRunStatus.Starting => QueuedStage,
            TrainingRunStatus.Succeeded or TrainingRunStatus.Cancelled => FinishedStage,
            TrainingRunStatus.Failed => EvaluationStage,
            _ => TrainingStage
        };
    }

    private static IReadOnlyList<string> MergeWarnings(
        IReadOnlyList<string> warnings,
        IReadOnlyList<string> cleanupWarnings)
    {
        return warnings
            .Concat(cleanupWarnings)
            .Where(warning => !string.IsNullOrWhiteSpace(warning))
            .Select(warning => warning.Trim())
            .Distinct(StringComparer.Ordinal)
            .ToArray();
    }
}
