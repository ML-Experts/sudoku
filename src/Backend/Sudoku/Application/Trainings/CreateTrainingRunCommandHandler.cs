using MediatR;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Datasets;
using Sudoku.Application.Ml;
using Sudoku.Application.ModelsRegistry;

namespace Sudoku.Application.Trainings;

public sealed class CreateTrainingRunCommandHandler
    : IRequestHandler<CreateTrainingRunCommand, CreateTrainingRunCommandResultDto>
{
    private static readonly HashSet<string> ActiveStatuses = new(StringComparer.OrdinalIgnoreCase)
    {
        "starting",
        "queued",
        "running",
        "cancelling"
    };

    private const int MaxReservationAttempts = 10;
    private const string QueuedStatus = "queued";
    private const string StartingStatus = "starting";
    private const string FailedStatus = "failed";
    private const string ArtifactsDirectoryName = "artifacts";

    private readonly ITrainingRunsGateway _trainingRunsGateway;
    private readonly IModelsRegistryGateway _modelsRegistryGateway;
    private readonly IProcessedDatasetsGateway _processedDatasetsGateway;
    private readonly IMlTrainingsGateway _mlTrainingsGateway;
    private readonly ITrainingEventsPathProvider _trainingEventsPathProvider;
    private readonly ITrainingRunNameGenerator _trainingRunNameGenerator;
    private readonly TrainingDefaultsOptions _trainingDefaultsOptions;
    private readonly TrainingsStorageOptions _trainingsStorageOptions;
    private readonly ModelsRegistryStorageOptions _modelsRegistryStorageOptions;
    private readonly DatasetsPreparationOptions _datasetsPreparationOptions;
    private readonly TimeProvider _timeProvider;

    public CreateTrainingRunCommandHandler(
        ITrainingRunsGateway trainingRunsGateway,
        IModelsRegistryGateway modelsRegistryGateway,
        IProcessedDatasetsGateway processedDatasetsGateway,
        IMlTrainingsGateway mlTrainingsGateway,
        ITrainingEventsPathProvider trainingEventsPathProvider,
        ITrainingRunNameGenerator trainingRunNameGenerator,
        IOptions<TrainingDefaultsOptions> trainingDefaultsOptions,
        IOptions<TrainingsStorageOptions> trainingsStorageOptions,
        IOptions<ModelsRegistryStorageOptions> modelsRegistryStorageOptions,
        IOptions<DatasetsPreparationOptions> datasetsPreparationOptions,
        TimeProvider timeProvider)
    {
        _trainingRunsGateway = trainingRunsGateway;
        _modelsRegistryGateway = modelsRegistryGateway;
        _processedDatasetsGateway = processedDatasetsGateway;
        _mlTrainingsGateway = mlTrainingsGateway;
        _trainingEventsPathProvider = trainingEventsPathProvider;
        _trainingRunNameGenerator = trainingRunNameGenerator;
        _trainingDefaultsOptions = trainingDefaultsOptions.Value;
        _trainingsStorageOptions = trainingsStorageOptions.Value;
        _modelsRegistryStorageOptions = modelsRegistryStorageOptions.Value;
        _datasetsPreparationOptions = datasetsPreparationOptions.Value;
        _timeProvider = timeProvider;
    }

    public async Task<CreateTrainingRunCommandResultDto> Handle(
        CreateTrainingRunCommand request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.BaseModelName)
            || string.IsNullOrWhiteSpace(request.ProcessedDatasetName))
        {
            throw new InvalidOperationException("CreateTrainingRunCommand must be validated before handler execution.");
        }

        var baseModelName = request.BaseModelName.Trim();
        var processedDatasetName = request.ProcessedDatasetName.Trim();

        await EnsureNoActiveRunAsync(cancellationToken);

        var baseModel = await ResolveBaseModelAsync(baseModelName, cancellationToken);
        var processedDataset = await ResolveProcessedDatasetAsync(processedDatasetName, cancellationToken);

        ValidateBaseModel(baseModel);
        ValidateProcessedDataset(processedDataset);
        ValidateProfileCompatibility(baseModel, processedDataset);

        var createdAtUtc = _timeProvider.GetUtcNow();
        var metadata = await ReserveTrainingRunAsync(
            createdAtUtc,
            baseModel,
            processedDataset,
            cancellationToken);

        try
        {
            var startResult = await _mlTrainingsGateway.StartTrainingAsync(
                BuildMlTrainingRequest(metadata, baseModel, processedDataset),
                cancellationToken);

            var queuedMetadata = metadata with
            {
                Status = QueuedStatus,
                UpdatedAtUtc = _timeProvider.GetUtcNow(),
                MlJobId = startResult.MlJobId
            };

            await _trainingRunsGateway.UpdateAsync(queuedMetadata, cancellationToken);
            return ToResult(queuedMetadata);
        }
        catch (Exception exception) when (exception is MlOperationFailedException
                                         or MlServiceUnavailableException
                                         or MlServiceTimeoutException)
        {
            await RollbackReservationAsync(metadata, exception, cancellationToken);
            throw;
        }
    }

    private async Task EnsureNoActiveRunAsync(CancellationToken cancellationToken)
    {
        var runs = await _trainingRunsGateway.ListAsync(cancellationToken);
        var activeRuns = runs
            .Where(run => ActiveStatuses.Contains(run.Status))
            .OrderByDescending(run => run.CreatedAtUtc)
            .ToArray();

        if (activeRuns.Length > 1)
        {
            throw new InvalidOperationException(
                "Detected more than one active training run. This violates the single active run invariant.");
        }

        if (activeRuns.Length == 1)
        {
            throw new ActiveTrainingRunAlreadyExistsException(activeRuns[0].RunName);
        }
    }

    private async Task<RegistryModelManifestDto> ResolveBaseModelAsync(
        string baseModelName,
        CancellationToken cancellationToken)
    {
        var baseModel = await _modelsRegistryGateway.GetByNameAsync(baseModelName, cancellationToken);
        return baseModel ?? throw new BaseModelNotFoundException(baseModelName);
    }

    private async Task<ProcessedDatasetMetadataDto> ResolveProcessedDatasetAsync(
        string processedDatasetName,
        CancellationToken cancellationToken)
    {
        var processedDataset = await _processedDatasetsGateway.GetByNameAsync(
            processedDatasetName,
            cancellationToken);

        return processedDataset ?? throw new ProcessedDatasetNotFoundException(processedDatasetName);
    }

    private static void ValidateBaseModel(RegistryModelManifestDto baseModel)
    {
        if (!baseModel.CanStartTraining || string.IsNullOrWhiteSpace(baseModel.PrimaryArtifactRelativePath))
        {
            throw new BaseModelCannotStartTrainingException(baseModel.Name);
        }
    }

    private static void ValidateProcessedDataset(ProcessedDatasetMetadataDto processedDataset)
    {
        var sampleCount = processedDataset.SampleCounts.Train
                          + processedDataset.SampleCounts.Val
                          + processedDataset.SampleCounts.Test;

        if (sampleCount <= 0)
        {
            throw new ProcessedDatasetCannotStartTrainingException(processedDataset.Name);
        }
    }

    private static void ValidateProfileCompatibility(
        RegistryModelManifestDto baseModel,
        ProcessedDatasetMetadataDto processedDataset)
    {
        if (!string.Equals(
                baseModel.InputProfile,
                processedDataset.PreprocessingProfile,
                StringComparison.Ordinal))
        {
            throw new TrainingProfileMismatchException(
                baseModel.InputProfile,
                processedDataset.PreprocessingProfile);
        }
    }

    private async Task<TrainingRunMetadataDto> ReserveTrainingRunAsync(
        DateTimeOffset createdAtUtc,
        RegistryModelManifestDto baseModel,
        ProcessedDatasetMetadataDto processedDataset,
        CancellationToken cancellationToken)
    {
        for (var attempt = 0; attempt < MaxReservationAttempts; attempt++)
        {
            var runName = _trainingRunNameGenerator.Generate(
                createdAtUtc,
                _trainingDefaultsOptions.RunNamePrefix,
                baseModel.Name,
                processedDataset.Name,
                attempt);

            var metadata = new TrainingRunMetadataDto(
                RunName: runName,
                Status: StartingStatus,
                CreatedAtUtc: createdAtUtc,
                BaseModelName: baseModel.Name,
                ProducedModelName: runName,
                ProcessedDatasetName: processedDataset.Name,
                TrainingMode: _trainingDefaultsOptions.TrainingMode,
                TrainingProfileName: _trainingDefaultsOptions.TrainingProfileName,
                AugmentationProfileName: _trainingDefaultsOptions.AugmentationProfileName,
                BenchmarkName: _trainingDefaultsOptions.BenchmarkName,
                Seed: _trainingDefaultsOptions.Seed,
                ProgressChannelUrl: $"/ws/trainings/{runName}",
                UpdatedAtUtc: createdAtUtc,
                SourceRevision: null,
                ReportStatus: null,
                Warnings: Array.Empty<string>(),
                MlJobId: null);

            if (await _trainingRunsGateway.TryCreateAsync(metadata, cancellationToken))
            {
                return metadata;
            }
        }

        throw new TrainingRunReservationException(
            "Nie udało się zarezerwować unikalnej nazwy runu treningowego.");
    }

    private StartMlTrainingRequestDto BuildMlTrainingRequest(
        TrainingRunMetadataDto metadata,
        RegistryModelManifestDto baseModel,
        ProcessedDatasetMetadataDto processedDataset)
    {
        var modelDirectoryPath = Path.GetFullPath(Path.Combine(
            _modelsRegistryStorageOptions.RegistryDirectoryPath,
            baseModel.Name));
        var producedModelDirectoryPath = Path.GetFullPath(Path.Combine(
            _modelsRegistryStorageOptions.RegistryDirectoryPath,
            metadata.ProducedModelName));

        return new StartMlTrainingRequestDto(
            RunName: metadata.RunName,
            BaseModel: new StartMlTrainingBaseModelDto(
                Name: baseModel.Name,
                ManifestPath: Path.GetFullPath(Path.Combine(modelDirectoryPath, "model.json")),
                PrimaryArtifactPath: Path.GetFullPath(Path.Combine(
                    modelDirectoryPath,
                    baseModel.PrimaryArtifactRelativePath!)),
                InputProfile: baseModel.InputProfile),
            Dataset: new StartMlTrainingDatasetDto(
                Name: processedDataset.Name,
                ArtifactPath: Path.GetFullPath(Path.Combine(
                    _datasetsPreparationOptions.ProcessedDatasetsDirectoryPath,
                    processedDataset.FileName)),
                PreprocessingProfile: processedDataset.PreprocessingProfile),
            Training: new StartMlTrainingSettingsDto(
                Mode: metadata.TrainingMode,
                TrainingProfileName: metadata.TrainingProfileName,
                AugmentationProfileName: metadata.AugmentationProfileName,
                BenchmarkName: metadata.BenchmarkName,
                Seed: metadata.Seed),
            Output: new StartMlTrainingOutputDto(
                RunDirectoryPath: Path.GetFullPath(Path.Combine(
                    _trainingsStorageOptions.RunsDirectoryPath,
                    metadata.RunName)),
                ReportsDirectoryPath: Path.GetFullPath(Path.Combine(
                    _trainingsStorageOptions.ReportsDirectoryPath,
                    metadata.RunName)),
                WorkingDirectoryPath: Path.GetFullPath(Path.Combine(
                    _trainingsStorageOptions.WorkingDirectoryPath,
                    metadata.RunName)),
                ProducedModelName: metadata.ProducedModelName,
                ProducedModelArtifactsDirectoryPath: Path.GetFullPath(Path.Combine(
                    producedModelDirectoryPath,
                    ArtifactsDirectoryName))),
            Callbacks: new StartMlTrainingCallbacksDto(
                EventsPath: _trainingEventsPathProvider.GetEventsPath(metadata.RunName)));
    }

    private async Task RollbackReservationAsync(
        TrainingRunMetadataDto metadata,
        Exception cause,
        CancellationToken cancellationToken)
    {
        try
        {
            await _trainingRunsGateway.DeleteAsync(metadata.RunName, cancellationToken);
        }
        catch (Exception deleteException) when (deleteException is IOException
                                               or UnauthorizedAccessException
                                               or InvalidOperationException)
        {
            var failedMetadata = metadata with
            {
                Status = FailedStatus,
                UpdatedAtUtc = _timeProvider.GetUtcNow(),
                Warnings = new[]
                {
                    "training_start_rollback_failed"
                }
            };

            try
            {
                await _trainingRunsGateway.UpdateAsync(failedMetadata, cancellationToken);
            }
            catch (Exception updateException) when (updateException is IOException
                                                   or UnauthorizedAccessException
                                                   or InvalidOperationException)
            {
                throw new TrainingRunStartFailedException(
                    "Nie udało się wycofać prowizorycznego rekordu runu po błędzie startu ML.",
                    new AggregateException(cause, deleteException, updateException));
            }
        }
    }

    private static CreateTrainingRunCommandResultDto ToResult(TrainingRunMetadataDto metadata)
    {
        return new CreateTrainingRunCommandResultDto(
            RunName: metadata.RunName,
            Status: metadata.Status,
            CreatedAtUtc: metadata.CreatedAtUtc,
            BaseModelName: metadata.BaseModelName,
            ProducedModelName: metadata.ProducedModelName,
            ProcessedDatasetName: metadata.ProcessedDatasetName,
            TrainingMode: metadata.TrainingMode,
            TrainingProfileName: metadata.TrainingProfileName,
            AugmentationProfileName: metadata.AugmentationProfileName,
            BenchmarkName: metadata.BenchmarkName,
            Seed: metadata.Seed,
            ProgressChannelUrl: metadata.ProgressChannelUrl);
    }
}
