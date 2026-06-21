using FluentValidation;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Datasets;
using Sudoku.Application.ModelsRegistry;
using Sudoku.Application.Trainings;

namespace Application.Tests;

public sealed class CreateTrainingRunCommandHandlerTests
{
    private static readonly DateTimeOffset FixedNow = DateTimeOffset.Parse("2026-05-19T18:34:00Z");

    [Fact]
    public async Task Handle_SavesEffectiveParametersAndForwardsThemToMl()
    {
        var trainingRunsGateway = new InMemoryTrainingRunsGateway();
        var mlTrainingsGateway = new StubMlTrainingsGateway();
        var handler = CreateHandler(
            trainingRunsGateway: trainingRunsGateway,
            mlTrainingsGateway: mlTrainingsGateway,
            modelsRegistryGateway: new StubModelsRegistryGateway(CreateBaseModel(architectureFamily: "cnn")),
            processedDatasetsGateway: new StubProcessedDatasetsGateway(CreateProcessedDataset()));

        var result = await handler.Handle(CreateCommand(), CancellationToken.None);

        Assert.NotNull(result.EffectiveParameters);
        Assert.Equal(20, result.EffectiveParameters!.Epochs);
        Assert.Equal(0.001, result.EffectiveParameters.LearningRate);
        Assert.Equal(32, result.EffectiveParameters.BatchSize);
        Assert.Equal(5, result.EffectiveParameters.EarlyStoppingPatience);
        Assert.Equal(0.001, result.EffectiveParameters.EarlyStoppingMinDelta);
        Assert.Equal(0, result.EffectiveParameters.WarmupEpochs);
        Assert.Equal(3, result.EffectiveParameters.LrSchedulerPatience);
        Assert.Equal(0.5, result.EffectiveParameters.LrSchedulerFactor);
        Assert.Equal("all", result.EffectiveParameters.FineTuningPolicy);
        Assert.True(result.EffectiveParameters.UseBestCheckpoint);

        var metadata = Assert.Single(trainingRunsGateway.Items.Values);
        Assert.NotNull(metadata.EffectiveParameters);
        Assert.Equal(20, metadata.EffectiveParameters!.Epochs);
        Assert.Equal(0.001, metadata.EffectiveParameters.EarlyStoppingMinDelta);
        Assert.Equal(0, metadata.EffectiveParameters.WarmupEpochs);
        Assert.Equal("all", metadata.EffectiveParameters.FineTuningPolicy);
        Assert.True(metadata.EffectiveParameters.UseBestCheckpoint);

        Assert.NotNull(mlTrainingsGateway.LastRequest);
        Assert.Equal(
            20,
            mlTrainingsGateway.LastRequest!.ResolvedConfiguration.TrainingParameters.Epochs);
        Assert.Equal(
            0.001,
            mlTrainingsGateway.LastRequest.ResolvedConfiguration.TrainingParameters.LearningRate);
        Assert.Equal(
            32,
            mlTrainingsGateway.LastRequest.ResolvedConfiguration.TrainingParameters.BatchSize);
        Assert.Equal(
            5,
            mlTrainingsGateway.LastRequest.ResolvedConfiguration.TrainingParameters.EarlyStoppingPatience);
        Assert.Equal(
            0.001,
            mlTrainingsGateway.LastRequest.ResolvedConfiguration.TrainingParameters.EarlyStoppingMinDelta);
        Assert.Equal(
            0,
            mlTrainingsGateway.LastRequest.ResolvedConfiguration.TrainingParameters.WarmupEpochs);
        Assert.Equal(
            3,
            mlTrainingsGateway.LastRequest.ResolvedConfiguration.TrainingParameters.LrSchedulerPatience);
        Assert.Equal(
            0.5,
            mlTrainingsGateway.LastRequest.ResolvedConfiguration.TrainingParameters.LrSchedulerFactor);
        Assert.Equal(
            "all",
            mlTrainingsGateway.LastRequest.ResolvedConfiguration.TrainingParameters.FineTuningPolicy);
        Assert.True(
            mlTrainingsGateway.LastRequest.ResolvedConfiguration.TrainingParameters.UseBestCheckpoint);
    }

    [Fact]
    public async Task Handle_ForwardsUseBestCheckpointFalseToMl()
    {
        var trainingRunsGateway = new InMemoryTrainingRunsGateway();
        var mlTrainingsGateway = new StubMlTrainingsGateway();
        var handler = CreateHandler(
            trainingRunsGateway: trainingRunsGateway,
            mlTrainingsGateway: mlTrainingsGateway,
            modelsRegistryGateway: new StubModelsRegistryGateway(CreateBaseModel(architectureFamily: "cnn")),
            processedDatasetsGateway: new StubProcessedDatasetsGateway(CreateProcessedDataset()));

        var result = await handler.Handle(
            CreateCommand(trainingParameters: CreateTrainingParameters(UseBestCheckpoint: false)),
            CancellationToken.None);

        Assert.NotNull(result.EffectiveParameters);
        Assert.False(result.EffectiveParameters!.UseBestCheckpoint);

        var metadata = Assert.Single(trainingRunsGateway.Items.Values);
        Assert.NotNull(metadata.EffectiveParameters);
        Assert.False(metadata.EffectiveParameters!.UseBestCheckpoint);

        Assert.NotNull(mlTrainingsGateway.LastRequest);
        Assert.False(
            mlTrainingsGateway.LastRequest!.ResolvedConfiguration.TrainingParameters.UseBestCheckpoint);
    }

    [Fact]
    public async Task Handle_UsesDefaultEarlyStoppingMinDelta_WhenParameterIsMissing()
    {
        var trainingRunsGateway = new InMemoryTrainingRunsGateway();
        var mlTrainingsGateway = new StubMlTrainingsGateway();
        var handler = CreateHandler(
            trainingRunsGateway: trainingRunsGateway,
            mlTrainingsGateway: mlTrainingsGateway,
            modelsRegistryGateway: new StubModelsRegistryGateway(CreateBaseModel(architectureFamily: "cnn")),
            processedDatasetsGateway: new StubProcessedDatasetsGateway(CreateProcessedDataset()));

        var result = await handler.Handle(
            CreateCommand(trainingParameters: CreateTrainingParameters(EarlyStoppingMinDelta: null)),
            CancellationToken.None);

        Assert.NotNull(result.EffectiveParameters);
        Assert.Equal(0.001, result.EffectiveParameters!.EarlyStoppingMinDelta);

        var metadata = Assert.Single(trainingRunsGateway.Items.Values);
        Assert.NotNull(metadata.EffectiveParameters);
        Assert.Equal(0.001, metadata.EffectiveParameters!.EarlyStoppingMinDelta);

        Assert.NotNull(mlTrainingsGateway.LastRequest);
        Assert.Equal(
            0.001,
            mlTrainingsGateway.LastRequest!.ResolvedConfiguration.TrainingParameters.EarlyStoppingMinDelta);
    }

    [Fact]
    public async Task Handle_UsesDefaultWarmupEpochs_WhenParameterIsMissing()
    {
        var trainingRunsGateway = new InMemoryTrainingRunsGateway();
        var mlTrainingsGateway = new StubMlTrainingsGateway();
        var handler = CreateHandler(
            trainingRunsGateway: trainingRunsGateway,
            mlTrainingsGateway: mlTrainingsGateway,
            modelsRegistryGateway: new StubModelsRegistryGateway(CreateBaseModel(architectureFamily: "cnn")),
            processedDatasetsGateway: new StubProcessedDatasetsGateway(CreateProcessedDataset()));

        var result = await handler.Handle(
            CreateCommand(trainingParameters: CreateTrainingParameters(WarmupEpochs: null)),
            CancellationToken.None);

        Assert.NotNull(result.EffectiveParameters);
        Assert.Equal(0, result.EffectiveParameters!.WarmupEpochs);

        var metadata = Assert.Single(trainingRunsGateway.Items.Values);
        Assert.NotNull(metadata.EffectiveParameters);
        Assert.Equal(0, metadata.EffectiveParameters!.WarmupEpochs);

        Assert.NotNull(mlTrainingsGateway.LastRequest);
        Assert.Equal(
            0,
            mlTrainingsGateway.LastRequest!.ResolvedConfiguration.TrainingParameters.WarmupEpochs);
    }

    [Fact]
    public async Task Handle_AllowsStart_WhenCancellingRunExceededRecoveryTimeout()
    {
        var trainingRunsGateway = new InMemoryTrainingRunsGateway();
        trainingRunsGateway.Items["stale-run"] = new TrainingRunMetadataDto(
            RunName: "stale-run",
            Status: "cancelling",
            CreatedAtUtc: FixedNow.AddMinutes(-30),
            BaseModelName: "cnn-bootstrap",
            ProducedModelName: "stale-model",
            ProcessedDatasetName: "digits",
            TrainingMode: "fineTuning",
            TrainingProfileName: "internal-default-v1",
            AugmentationProfileName: "digits-light-v1",
            BenchmarkName: "sudoku-benchmark-v1",
            Seed: 1234,
            ProgressChannelUrl: "/ws/trainings/stale-run",
            UpdatedAtUtc: FixedNow.AddMinutes(-20),
            Stage: "evaluation",
            LastAcceptedSequence: 10,
            LastEventType: "statusChanged",
            LastEventMessage: "Training evaluation started.",
            LastEventOccurredAtUtc: FixedNow.AddMinutes(-20));

        var recovery = new TrainingRunCancellationRecovery(
            trainingRunsGateway,
            new StubTrainingArtifactsCleanupGateway(),
            new RecordingTrainingRunEventPublisher(),
            new InMemoryTrainingRunEventLockProvider(),
            Options.Create(new TrainingRecoveryOptions
            {
                StaleCancellingTimeoutSeconds = 300
            }),
            new FixedTimeProvider(FixedNow));
        var handler = CreateHandler(
            trainingRunsGateway: trainingRunsGateway,
            trainingRunCancellationRecovery: recovery);

        var result = await handler.Handle(CreateCommand(), CancellationToken.None);

        Assert.Equal("train-cnn-bootstrap-digits", result.RunName);
        Assert.Equal("cancelled", trainingRunsGateway.Items["stale-run"].Status);
        Assert.Equal("finished", trainingRunsGateway.Items["stale-run"].Stage);
        Assert.Equal(11L, trainingRunsGateway.Items["stale-run"].LastAcceptedSequence);
        Assert.Contains(
            "stale_cancelling_auto_cancelled",
            trainingRunsGateway.Items["stale-run"].Warnings ?? Array.Empty<string>());
    }

    [Fact]
    public async Task Handle_ThrowsValidationException_WhenHeadOnlyIsRequestedForNonResnetModel()
    {
        var handler = CreateHandler(
            modelsRegistryGateway: new StubModelsRegistryGateway(CreateBaseModel(architectureFamily: "cnn")),
            processedDatasetsGateway: new StubProcessedDatasetsGateway(CreateProcessedDataset()));

        var exception = await Assert.ThrowsAsync<ValidationException>(() => handler.Handle(
            CreateCommand(trainingParameters: CreateTrainingParameters(FineTuningPolicy: "head-only")),
            CancellationToken.None));

        var failure = Assert.Single(exception.Errors);
        Assert.Equal(CreateTrainingRunErrorTypes.InvalidRequest, failure.ErrorCode);
        Assert.Equal("TrainingParameters.FineTuningPolicy", failure.PropertyName);
    }

    [Fact]
    public async Task Handle_DoesNotOverwriteTerminalEventThatArrivedBeforeQueuedStatusWasPersisted()
    {
        var trainingRunsGateway = new InMemoryTrainingRunsGateway();
        var mlTrainingsGateway = new StubMlTrainingsGateway(delayCompletion: true);
        var lockProvider = new InMemoryTrainingRunEventLockProvider();
        var handler = CreateHandler(
            trainingRunsGateway: trainingRunsGateway,
            mlTrainingsGateway: mlTrainingsGateway,
            trainingRunEventLockProvider: lockProvider);

        var handleTask = handler.Handle(CreateCommand(), CancellationToken.None);
        await mlTrainingsGateway.WaitForStartCallAsync();

        var runName = Assert.Single(trainingRunsGateway.Items.Keys);
        await using (await lockProvider.AcquireAsync(runName, CancellationToken.None))
        {
            var terminalMetadata = trainingRunsGateway.Items[runName] with
            {
                Status = "failed",
                UpdatedAtUtc = FixedNow,
                Stage = "training",
                LastAcceptedSequence = 2,
                LastEventType = "failed",
                LastEventMessage = "Training failed before first running event.",
                LastEventOccurredAtUtc = FixedNow,
                FailureReason = "Training failed before first running event.",
                FailureErrorType = "training_run_failed",
                FinishedAtUtc = FixedNow
            };
            trainingRunsGateway.Items[runName] = terminalMetadata;
            mlTrainingsGateway.AllowCompletion();
        }

        var result = await handleTask;

        Assert.Equal("failed", result.Status);
        Assert.Equal("failed", trainingRunsGateway.Items[runName].Status);
        Assert.Equal("failed", trainingRunsGateway.Items[runName].LastEventType);
        Assert.Equal(2L, trainingRunsGateway.Items[runName].LastAcceptedSequence);
    }

    private static CreateTrainingRunCommandHandler CreateHandler(
        InMemoryTrainingRunsGateway? trainingRunsGateway = null,
        StubMlTrainingsGateway? mlTrainingsGateway = null,
        StubModelsRegistryGateway? modelsRegistryGateway = null,
        StubProcessedDatasetsGateway? processedDatasetsGateway = null,
        ITrainingRunCancellationRecovery? trainingRunCancellationRecovery = null,
        ITrainingRunEventLockProvider? trainingRunEventLockProvider = null)
    {
        return new CreateTrainingRunCommandHandler(
            trainingRunsGateway ?? new InMemoryTrainingRunsGateway(),
            modelsRegistryGateway ?? new StubModelsRegistryGateway(CreateBaseModel(architectureFamily: "cnn")),
            processedDatasetsGateway ?? new StubProcessedDatasetsGateway(CreateProcessedDataset()),
            mlTrainingsGateway ?? new StubMlTrainingsGateway(),
            trainingRunCancellationRecovery ?? new StubTrainingRunCancellationRecovery(),
            new StubTrainingEventsPathProvider(),
            trainingRunEventLockProvider ?? new InMemoryTrainingRunEventLockProvider(),
            new StubTrainingRunNameGenerator("train-cnn-bootstrap-digits"),
            Options.Create(new TrainingDefaultsOptions
            {
                RunNamePrefix = "train",
                TrainingMode = "fineTuning",
                TrainingProfileName = "internal-default-v1",
                AugmentationProfileName = "digits-light-v1",
                BenchmarkName = "sudoku-benchmark-v1",
                Seed = 1234
            }),
            Options.Create(new TrainingsStorageOptions
            {
                RunsDirectoryPath = "/tmp/trainings/runs",
                ReportsDirectoryPath = "/tmp/trainings/reports",
                MetadataDirectoryPath = "/tmp/trainings/metadata",
                WorkingDirectoryPath = "/tmp/trainings/tmp"
            }),
            Options.Create(new ModelsRegistryStorageOptions
            {
                RegistryDirectoryPath = "/tmp/models/registry"
            }),
            Options.Create(new DatasetsPreparationOptions
            {
                BoardsSubdirectory = "boards",
                DigitsSubdirectory = "digits",
                ProcessedDatasetsDirectoryPath = "/tmp/data/processed",
                TemporaryArtifactsDirectoryPath = "/tmp/data/tmp",
                DefaultPreprocessingProfile = "default-28x28-v1"
            }),
            new FixedTimeProvider(FixedNow));
    }

    private static CreateTrainingRunCommand CreateCommand(
        string? baseModelName = "cnn-bootstrap",
        string? processedDatasetName = "digits",
        TrainingRunRequestedParametersDto? trainingParameters = null)
    {
        return new CreateTrainingRunCommand(
            BaseModelName: baseModelName,
            ProcessedDatasetName: processedDatasetName,
            TrainingParameters: trainingParameters ?? CreateTrainingParameters());
    }

    private static TrainingRunRequestedParametersDto CreateTrainingParameters(
        int? Epochs = 20,
        double? LearningRate = 0.001,
        int? BatchSize = 32,
        int? EarlyStoppingPatience = 5,
        double? EarlyStoppingMinDelta = 0.001,
        int? WarmupEpochs = 0,
        int? LrSchedulerPatience = 3,
        double? LrSchedulerFactor = 0.5,
        string? FineTuningPolicy = "all",
        bool? UseBestCheckpoint = true)
    {
        return new TrainingRunRequestedParametersDto(
            Epochs: Epochs,
            LearningRate: LearningRate,
            BatchSize: BatchSize,
            EarlyStoppingPatience: EarlyStoppingPatience,
            EarlyStoppingMinDelta: EarlyStoppingMinDelta,
            WarmupEpochs: WarmupEpochs,
            LrSchedulerPatience: LrSchedulerPatience,
            LrSchedulerFactor: LrSchedulerFactor,
            FineTuningPolicy: FineTuningPolicy,
            UseBestCheckpoint: UseBestCheckpoint);
    }

    private static RegistryModelManifestDto CreateBaseModel(string architectureFamily)
    {
        return new RegistryModelManifestDto(
            Name: "cnn-bootstrap",
            DisplayName: "CNN Bootstrap",
            SourceType: "bootstrap",
            SourceRunName: null,
            ParentModelName: null,
            TrainingMode: "fineTuning",
            Framework: "pytorch",
            ArchitectureType: "custom-cnn-v1",
            ArchitectureFamily: architectureFamily,
            ArchitectureNumClasses: 10,
            ArchitectureInputChannels: 1,
            ArchitectureInputHeight: 28,
            ArchitectureInputWidth: 28,
            InputProfile: "default-28x28-v1",
            TrainingProfileName: "internal-default-v1",
            AugmentationProfileName: "digits-light-v1",
            CreatedAtUtc: FixedNow.AddDays(-1),
            CanStartTraining: true,
            CanUseForInference: true,
            PrimaryArtifactRelativePath: "artifacts/model.pt",
            ArtifactFormat: "pytorch-state-dict",
            Warnings: Array.Empty<string>());
    }

    private static ProcessedDatasetMetadataDto CreateProcessedDataset()
    {
        return new ProcessedDatasetMetadataDto(
            Name: "digits",
            PreparationName: "preparation-001",
            FileName: "digits.npz",
            PreprocessingProfile: "default-28x28-v1",
            CreatedAtUtc: FixedNow.AddDays(-1),
            Sources: Array.Empty<SelectedRawDatasetSourceDto>(),
            SampleCounts: new SplitSampleCountsDto(Train: 10, Val: 4, Test: 2),
            SourceReports: Array.Empty<ProcessedDatasetSourceReportDto>(),
            Warnings: Array.Empty<string>());
    }

    private sealed class StubTrainingRunCancellationRecovery : ITrainingRunCancellationRecovery
    {
        public Task RecoverAsync(CancellationToken cancellationToken = default)
        {
            return Task.CompletedTask;
        }
    }

    private sealed class StubTrainingArtifactsCleanupGateway : ITrainingArtifactsCleanupGateway
    {
        public Task<IReadOnlyList<string>> CleanupFailedOrCancelledRunAsync(
            TrainingRunMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            return Task.FromResult<IReadOnlyList<string>>(Array.Empty<string>());
        }
    }

    private sealed class RecordingTrainingRunEventPublisher : ITrainingRunEventPublisher
    {
        public List<TrainingRunMetadataDto> PublishedMetadata { get; } = [];

        public Task PublishAsync(
            TrainingRunMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            PublishedMetadata.Add(metadata);
            return Task.CompletedTask;
        }
    }

    private sealed class InMemoryTrainingRunsGateway : ITrainingRunsGateway
    {
        public Dictionary<string, TrainingRunMetadataDto> Items { get; } = new(StringComparer.Ordinal);

        public Task<IReadOnlyList<TrainingRunMetadataDto>> ListAsync(CancellationToken cancellationToken = default)
        {
            return Task.FromResult<IReadOnlyList<TrainingRunMetadataDto>>(Items.Values.ToArray());
        }

        public Task<TrainingRunMetadataDto?> GetByRunNameAsync(
            string runName,
            CancellationToken cancellationToken = default)
        {
            Items.TryGetValue(runName, out var metadata);
            return Task.FromResult(metadata);
        }

        public Task<bool> TryCreateAsync(
            TrainingRunMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            var created = Items.TryAdd(metadata.RunName, metadata);
            return Task.FromResult(created);
        }

        public Task UpdateAsync(
            TrainingRunMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            Items[metadata.RunName] = metadata;
            return Task.CompletedTask;
        }

        public Task DeleteAsync(string runName, CancellationToken cancellationToken = default)
        {
            Items.Remove(runName);
            return Task.CompletedTask;
        }
    }

    private sealed class StubMlTrainingsGateway : IMlTrainingsGateway
    {
        private readonly bool _delayCompletion;
        public StartMlTrainingRequestDto? LastRequest { get; private set; }
        private readonly TaskCompletionSource<bool> _startCalled =
            new(TaskCreationOptions.RunContinuationsAsynchronously);
        private readonly TaskCompletionSource<bool> _allowCompletion =
            new(TaskCreationOptions.RunContinuationsAsynchronously);

        public StubMlTrainingsGateway(bool delayCompletion = false)
        {
            _delayCompletion = delayCompletion;
            if (!delayCompletion)
            {
                _allowCompletion.TrySetResult(true);
            }
        }

        public Task<StartMlTrainingResultDto> StartTrainingAsync(
            StartMlTrainingRequestDto request,
            CancellationToken cancellationToken = default)
        {
            LastRequest = request;
            _startCalled.TrySetResult(true);
            if (_delayCompletion)
            {
                return WaitForCompletionAsync(cancellationToken);
            }

            return Task.FromResult(new StartMlTrainingResultDto(
                AcceptedAtUtc: FixedNow,
                MlJobId: "ml-job-01",
                Status: "queued"));
        }

        public Task WaitForStartCallAsync()
        {
            return _startCalled.Task;
        }

        public void AllowCompletion()
        {
            _allowCompletion.TrySetResult(true);
        }

        public Task<CancelMlTrainingResultDto> CancelTrainingAsync(
            CancelMlTrainingRequestDto request,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        private async Task<StartMlTrainingResultDto> WaitForCompletionAsync(
            CancellationToken cancellationToken)
        {
            await _allowCompletion.Task.WaitAsync(cancellationToken);
            return new StartMlTrainingResultDto(
                AcceptedAtUtc: FixedNow,
                MlJobId: "ml-job-01",
                Status: "queued");
        }
    }

    private sealed class StubModelsRegistryGateway : IModelsRegistryGateway
    {
        private readonly RegistryModelManifestDto _model;

        public StubModelsRegistryGateway(RegistryModelManifestDto model)
        {
            _model = model;
        }

        public Task<IReadOnlyList<RegistryModelManifestDto>> ListAsync(
            CancellationToken cancellationToken = default)
        {
            return Task.FromResult<IReadOnlyList<RegistryModelManifestDto>>(new[] { _model });
        }

        public Task<RegistryModelManifestDto?> GetByNameAsync(
            string modelName,
            CancellationToken cancellationToken = default)
        {
            return Task.FromResult<RegistryModelManifestDto?>(
                string.Equals(modelName, _model.Name, StringComparison.Ordinal)
                    ? _model
                    : null);
        }

        public Task FinalizeTrainedModelAsync(
            FinalizeTrainedModelManifestDto manifest,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }
    }

    private sealed class StubProcessedDatasetsGateway : IProcessedDatasetsGateway
    {
        private readonly ProcessedDatasetMetadataDto _dataset;

        public StubProcessedDatasetsGateway(ProcessedDatasetMetadataDto dataset)
        {
            _dataset = dataset;
        }

        public Task<bool> IsProcessedDatasetNameAvailableAsync(
            string datasetName,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task PromotePreparedArtifactAsync(
            string datasetName,
            string targetFileName,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task SaveMetadataAsync(
            ProcessedDatasetMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task<IReadOnlyList<ProcessedDatasetMetadataDto>> ListAsync(
            CancellationToken cancellationToken = default)
        {
            return Task.FromResult<IReadOnlyList<ProcessedDatasetMetadataDto>>(new[] { _dataset });
        }

        public Task<ProcessedDatasetMetadataDto?> GetByNameAsync(
            string datasetName,
            CancellationToken cancellationToken = default)
        {
            return Task.FromResult<ProcessedDatasetMetadataDto?>(
                string.Equals(datasetName, _dataset.Name, StringComparison.Ordinal)
                    ? _dataset
                    : null);
        }
    }

    private sealed class StubTrainingEventsPathProvider : ITrainingEventsPathProvider
    {
        public string GetEventsPath(string runName)
        {
            return $"/internal/ml/trainings/{runName}/events";
        }
    }

    private sealed class StubTrainingRunNameGenerator : ITrainingRunNameGenerator
    {
        private readonly string _runName;

        public StubTrainingRunNameGenerator(string runName)
        {
            _runName = runName;
        }

        public string Generate(
            DateTimeOffset createdAtUtc,
            string runNamePrefix,
            string baseModelName,
            string processedDatasetName,
            int attempt)
        {
            return attempt == 0
                ? _runName
                : $"{_runName}-{attempt}";
        }
    }

    private sealed class FixedTimeProvider : TimeProvider
    {
        private readonly DateTimeOffset _utcNow;

        public FixedTimeProvider(DateTimeOffset utcNow)
        {
            _utcNow = utcNow;
        }

        public override DateTimeOffset GetUtcNow()
        {
            return _utcNow;
        }
    }
}
