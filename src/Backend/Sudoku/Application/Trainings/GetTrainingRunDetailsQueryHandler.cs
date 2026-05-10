using MediatR;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Datasets;
using Sudoku.Application.ModelsRegistry;
using Sudoku.Models.Trainings;

namespace Sudoku.Application.Trainings;

public sealed class GetTrainingRunDetailsQueryHandler
    : IRequestHandler<GetTrainingRunDetailsQuery, GetTrainingRunDetailsQueryResultDto>
{
    private const string DatasetMetadataMissingWarning = "processed_dataset_metadata_missing";

    private readonly ITrainingRunsGateway _trainingRunsGateway;
    private readonly IModelsRegistryGateway _modelsRegistryGateway;
    private readonly IProcessedDatasetsGateway _processedDatasetsGateway;
    private readonly ITrainingReportsGateway _trainingReportsGateway;

    public GetTrainingRunDetailsQueryHandler(
        ITrainingRunsGateway trainingRunsGateway,
        IModelsRegistryGateway modelsRegistryGateway,
        IProcessedDatasetsGateway processedDatasetsGateway,
        ITrainingReportsGateway trainingReportsGateway)
    {
        _trainingRunsGateway = trainingRunsGateway;
        _modelsRegistryGateway = modelsRegistryGateway;
        _processedDatasetsGateway = processedDatasetsGateway;
        _trainingReportsGateway = trainingReportsGateway;
    }

    public async Task<GetTrainingRunDetailsQueryResultDto> Handle(
        GetTrainingRunDetailsQuery request,
        CancellationToken cancellationToken)
    {
        var runName = request.RunName?.Trim()
                      ?? throw new InvalidOperationException(
                          "GetTrainingRunDetailsQuery must be validated before handler execution.");

        var metadata = await _trainingRunsGateway.GetByRunNameAsync(runName, cancellationToken)
                       ?? throw new TrainingRunDetailsNotFoundException(runName);

        EnsureRequiredMetadata(metadata, runName);

        var baseModel = await LoadBaseModelAsync(metadata, cancellationToken);
        var producedModel = await LoadProducedModelAsync(metadata, cancellationToken);
        var dataset = await _processedDatasetsGateway.GetByNameAsync(metadata.ProcessedDatasetName, cancellationToken);
        var warnings = BuildWarnings(metadata, dataset);
        var reportStatus = ResolveReportStatus(metadata);

        var report = string.Equals(reportStatus, TrainingReportStatus.Ready, StringComparison.Ordinal)
            ? await LoadReadyReportAsync(metadata, cancellationToken)
            : BuildEmptyReport(reportStatus);

        return new GetTrainingRunDetailsQueryResultDto(
            new TrainingRunDetailsDto(
                RunName: metadata.RunName,
                Status: metadata.Status,
                Stage: metadata.Stage,
                CreatedAtUtc: metadata.CreatedAtUtc,
                StartedAtUtc: metadata.StartedAtUtc,
                FinishedAtUtc: metadata.FinishedAtUtc,
                BaseModel: ToModelReference(baseModel),
                ProducedModel: producedModel is null ? null : ToModelReference(producedModel),
                Dataset: ToDatasetDetails(metadata.ProcessedDatasetName, dataset),
                Configuration: new TrainingRunConfigurationDto(
                    TrainingMode: metadata.TrainingMode,
                    TrainingProfileName: metadata.TrainingProfileName,
                    AugmentationProfileName: metadata.AugmentationProfileName,
                    BenchmarkName: metadata.BenchmarkName,
                    Seed: metadata.Seed,
                    SourceRevision: metadata.SourceRevision),
                Progress: metadata.Progress,
                Report: report,
                Warnings: warnings));
    }

    private async Task<RegistryModelManifestDto> LoadBaseModelAsync(
        TrainingRunMetadataDto metadata,
        CancellationToken cancellationToken)
    {
        var baseModel = await _modelsRegistryGateway.GetByNameAsync(metadata.BaseModelName, cancellationToken);
        return baseModel ?? throw new TrainingRunDetailsConflictException(
            $"Model bazowy {metadata.BaseModelName} wskazany przez run {metadata.RunName} nie istnieje.");
    }

    private async Task<RegistryModelManifestDto?> LoadProducedModelAsync(
        TrainingRunMetadataDto metadata,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(metadata.ProducedModelName))
        {
            if (string.Equals(metadata.Status, TrainingRunStatus.Succeeded, StringComparison.OrdinalIgnoreCase))
            {
                throw new TrainingRunDetailsConflictException(
                    $"Run {metadata.RunName} zakończył się sukcesem, ale nie wskazuje modelu wynikowego.");
            }

            return null;
        }

        var producedModel = await _modelsRegistryGateway.GetByNameAsync(
            metadata.ProducedModelName,
            cancellationToken);

        if (producedModel is null)
        {
            if (string.Equals(metadata.Status, TrainingRunStatus.Succeeded, StringComparison.OrdinalIgnoreCase))
            {
                throw new TrainingRunDetailsConflictException(
                    $"Model wynikowy {metadata.ProducedModelName} dla runu {metadata.RunName} nie istnieje.");
            }

            return null;
        }

        EnsureProducedModelConsistent(metadata, producedModel);
        return producedModel;
    }

    private async Task<TrainingRunReportDto> LoadReadyReportAsync(
        TrainingRunMetadataDto metadata,
        CancellationToken cancellationToken)
    {
        var artifacts = metadata.ReportArtifacts
                        ?? throw new TrainingRunDetailsConflictException(
                            $"Run {metadata.RunName} deklaruje gotowy raport, ale nie zawiera referencji do artefaktów.");

        var summaryRelativePath = EnsureSafeRelativePath(artifacts.SummaryRelativePath, "summaryRelativePath");
        var metricsRelativePath = EnsureSafeRelativePath(artifacts.MetricsRelativePath, "metricsRelativePath");
        var confusionMatrixRelativePath = EnsureSafeRelativePath(
            artifacts.ConfusionMatrixRelativePath,
            "confusionMatrixRelativePath");

        try
        {
            return await _trainingReportsGateway.GetReportAsync(
                metadata.RunName,
                summaryRelativePath,
                metricsRelativePath,
                confusionMatrixRelativePath,
                cancellationToken);
        }
        catch (InvalidDataException exception)
        {
            throw new TrainingRunReportInvalidException(
                $"Raport runu {metadata.RunName} nie spełnia kontraktu publicznego.",
                exception);
        }
    }

    private static void EnsureRequiredMetadata(TrainingRunMetadataDto metadata, string requestedRunName)
    {
        if (!string.Equals(metadata.RunName, requestedRunName, StringComparison.Ordinal))
        {
            throw new TrainingRunDetailsConflictException(
                $"Metadane runu {requestedRunName} zawierają inną nazwę runu.");
        }

        EnsureRequired(metadata.RunName, nameof(metadata.RunName));
        EnsureRequired(metadata.Status, nameof(metadata.Status));
        EnsureRequired(metadata.BaseModelName, nameof(metadata.BaseModelName));
        EnsureRequired(metadata.ProcessedDatasetName, nameof(metadata.ProcessedDatasetName));
        EnsureRequired(metadata.TrainingMode, nameof(metadata.TrainingMode));
        EnsureRequired(metadata.TrainingProfileName, nameof(metadata.TrainingProfileName));
        EnsureRequired(metadata.AugmentationProfileName, nameof(metadata.AugmentationProfileName));
        EnsureRequired(metadata.BenchmarkName, nameof(metadata.BenchmarkName));

        if (metadata.CreatedAtUtc == default)
        {
            throw new TrainingRunDetailsConflictException(
                $"Metadane runu {metadata.RunName} nie zawierają poprawnego {nameof(metadata.CreatedAtUtc)}.");
        }
    }

    private static void EnsureProducedModelConsistent(
        TrainingRunMetadataDto metadata,
        RegistryModelManifestDto producedModel)
    {
        if (!string.IsNullOrWhiteSpace(producedModel.SourceRunName)
            && !string.Equals(producedModel.SourceRunName, metadata.RunName, StringComparison.Ordinal))
        {
            throw new TrainingRunDetailsConflictException(
                $"Model wynikowy {producedModel.Name} wskazuje inny sourceRunName niż run {metadata.RunName}.");
        }

        if (!string.IsNullOrWhiteSpace(producedModel.ParentModelName)
            && !string.Equals(producedModel.ParentModelName, metadata.BaseModelName, StringComparison.Ordinal))
        {
            throw new TrainingRunDetailsConflictException(
                $"Model wynikowy {producedModel.Name} wskazuje inny parentModelName niż model bazowy runu.");
        }
    }

    private static string ResolveReportStatus(TrainingRunMetadataDto metadata)
    {
        if (string.IsNullOrWhiteSpace(metadata.ReportStatus))
        {
            return TrainingRunStatus.IsActive(metadata.Status)
                ? TrainingReportStatus.Pending
                : TrainingReportStatus.Missing;
        }

        var status = metadata.ReportStatus.Trim();
        if (status is TrainingReportStatus.Ready
            or TrainingReportStatus.Missing
            or TrainingReportStatus.Corrupted
            or TrainingReportStatus.Pending)
        {
            return status;
        }

        throw new TrainingRunDetailsConflictException(
            $"Run {metadata.RunName} zawiera nieznany status raportu {status}.");
    }

    private static string EnsureSafeRelativePath(string? relativePath, string fieldName)
    {
        if (string.IsNullOrWhiteSpace(relativePath)
            || Path.IsPathRooted(relativePath)
            || relativePath.Split(
                    new[] { '/', '\\' },
                    StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
                .Any(segment => segment == ".."))
        {
            throw new TrainingRunDetailsConflictException(
                $"Referencja raportu {fieldName} musi być bezpieczną ścieżką względną.");
        }

        return relativePath.Trim();
    }

    private static IReadOnlyList<string> BuildWarnings(
        TrainingRunMetadataDto metadata,
        ProcessedDatasetMetadataDto? dataset)
    {
        return (metadata.Warnings ?? Array.Empty<string>())
            .Concat(dataset is null ? new[] { DatasetMetadataMissingWarning } : Array.Empty<string>())
            .Where(warning => !string.IsNullOrWhiteSpace(warning))
            .Select(warning => warning.Trim())
            .Distinct(StringComparer.Ordinal)
            .ToArray();
    }

    private static TrainingRunDatasetDetailsDto ToDatasetDetails(
        string processedDatasetName,
        ProcessedDatasetMetadataDto? dataset)
    {
        return new TrainingRunDatasetDetailsDto(
            ProcessedDatasetName: processedDatasetName,
            PreprocessingProfile: dataset?.PreprocessingProfile,
            SampleCounts: dataset is null
                ? null
                : new TrainingDatasetSampleCountsDto(
                    Train: dataset.SampleCounts.Train,
                    Val: dataset.SampleCounts.Val,
                    Test: dataset.SampleCounts.Test));
    }

    private static TrainingRunModelReferenceDto ToModelReference(RegistryModelManifestDto model)
    {
        return new TrainingRunModelReferenceDto(
            Name: model.Name,
            DisplayName: model.DisplayName,
            SourceType: model.SourceType,
            SourceRunName: model.SourceRunName,
            ParentModelName: model.ParentModelName,
            InputProfile: model.InputProfile,
            CanUseForInference: model.CanUseForInference,
            CanStartTraining: model.CanStartTraining);
    }

    private static TrainingRunReportDto BuildEmptyReport(string status)
    {
        return new TrainingRunReportDto(
            Status: status,
            Summary: null,
            PerClassMetrics: Array.Empty<TrainingClassMetricDto>(),
            History: Array.Empty<TrainingMetricHistoryPointDto>(),
            ConfusionMatrix: null);
    }

    private static void EnsureRequired(string? value, string fieldName)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new TrainingRunDetailsConflictException(
                $"Metadane runu treningowego nie zawierają wymaganego pola {fieldName}.");
        }
    }
}
