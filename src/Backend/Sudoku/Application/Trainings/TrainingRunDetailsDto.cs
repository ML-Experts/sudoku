namespace Sudoku.Application.Trainings;

public sealed record TrainingRunDetailsDto(
    string RunName,
    string Status,
    string? Stage,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset? StartedAtUtc,
    DateTimeOffset? FinishedAtUtc,
    TrainingRunModelReferenceDto BaseModel,
    TrainingRunModelReferenceDto? ProducedModel,
    TrainingRunDatasetDetailsDto Dataset,
    TrainingRunConfigurationDto Configuration,
    TrainingRunProgressDto? Progress,
    TrainingRunReportDto Report,
    IReadOnlyList<string> Warnings);

public sealed record TrainingRunModelReferenceDto(
    string Name,
    string DisplayName,
    string SourceType,
    string? SourceRunName,
    string? ParentModelName,
    string InputProfile,
    bool CanUseForInference,
    bool CanStartTraining);

public sealed record TrainingRunDatasetDetailsDto(
    string ProcessedDatasetName,
    string? PreprocessingProfile,
    TrainingDatasetSampleCountsDto? SampleCounts);

public sealed record TrainingDatasetSampleCountsDto(
    int Train,
    int Val,
    int Test);

public sealed record TrainingRunConfigurationDto(
    string TrainingMode,
    string TrainingProfileName,
    string AugmentationProfileName,
    string BenchmarkName,
    int Seed,
    string? SourceRevision);

public sealed record TrainingRunReportDto(
    string Status,
    TrainingReportSummaryDto? Summary,
    IReadOnlyList<TrainingClassMetricDto> PerClassMetrics,
    IReadOnlyList<TrainingMetricHistoryPointDto> History,
    TrainingConfusionMatrixDto? ConfusionMatrix);

public sealed record TrainingReportSummaryDto(
    decimal Accuracy,
    decimal PrecisionMacro,
    decimal RecallMacro,
    decimal F1Macro,
    decimal? TrainingDurationSeconds,
    decimal? AverageInferenceTimeMs);

public sealed record TrainingClassMetricDto(
    string Label,
    decimal Precision,
    decimal Recall,
    decimal F1,
    int Support);

public sealed record TrainingMetricHistoryPointDto(
    int Epoch,
    decimal? TrainLoss,
    decimal? ValidationLoss,
    decimal? TrainAccuracy,
    decimal? ValidationAccuracy);

public sealed record TrainingConfusionMatrixDto(
    IReadOnlyList<string> ClassNames,
    IReadOnlyList<IReadOnlyList<int>> Matrix);
