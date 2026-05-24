namespace Sudoku.Contracts;

public sealed record TrainingRunDetailsApiResponse(
    string RunName,
    string Status,
    string? Stage,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset? StartedAtUtc,
    DateTimeOffset? FinishedAtUtc,
    TrainingRunModelReferenceApiResponse BaseModel,
    TrainingRunModelReferenceApiResponse? ProducedModel,
    TrainingRunDatasetDetailsApiResponse Dataset,
    TrainingRunConfigurationApiResponse Configuration,
    TrainingRunProgressApiResponse? Progress,
    TrainingRunReportApiResponse Report,
    IReadOnlyList<string> Warnings);

public sealed record TrainingRunModelReferenceApiResponse(
    string Name,
    string DisplayName,
    string SourceType,
    string? SourceRunName,
    string? ParentModelName,
    string InputProfile,
    bool CanUseForInference,
    bool CanStartTraining);

public sealed record TrainingRunDatasetDetailsApiResponse(
    string ProcessedDatasetName,
    string? PreprocessingProfile,
    TrainingDatasetSampleCountsApiResponse? SampleCounts);

public sealed record TrainingDatasetSampleCountsApiResponse(
    int Train,
    int Val,
    int Test);

public sealed record TrainingRunConfigurationApiResponse(
    string TrainingMode,
    string TrainingProfileName,
    string AugmentationProfileName,
    string BenchmarkName,
    int Seed,
    TrainingRunEffectiveParametersApiResponse? EffectiveParameters,
    string? SourceRevision);

public sealed record TrainingRunReportApiResponse(
    string Status,
    TrainingReportSummaryApiResponse? Summary,
    IReadOnlyList<TrainingClassMetricApiResponse> PerClassMetrics,
    IReadOnlyList<TrainingMetricHistoryPointApiResponse> History,
    TrainingConfusionMatrixApiResponse? ConfusionMatrix);

public sealed record TrainingReportSummaryApiResponse(
    decimal Accuracy,
    decimal PrecisionMacro,
    decimal RecallMacro,
    decimal F1Macro,
    decimal? TrainingDurationSeconds,
    decimal? AverageInferenceTimeMs);

public sealed record TrainingClassMetricApiResponse(
    string Label,
    decimal Precision,
    decimal Recall,
    decimal F1,
    int Support);

public sealed record TrainingMetricHistoryPointApiResponse(
    int Epoch,
    decimal? TrainLoss,
    decimal? ValidationLoss,
    decimal? TrainAccuracy,
    decimal? ValidationAccuracy);

public sealed record TrainingConfusionMatrixApiResponse(
    IReadOnlyList<string> ClassNames,
    IReadOnlyList<IReadOnlyList<int>> Matrix);
