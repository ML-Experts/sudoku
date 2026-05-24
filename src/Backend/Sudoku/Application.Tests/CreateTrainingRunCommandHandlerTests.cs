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
        Assert.Equal(3, result.EffectiveParameters.LrSchedulerPatience);
        Assert.Equal(0.5, result.EffectiveParameters.LrSchedulerFactor);
        Assert.Equal("all", result.EffectiveParameters.FineTuningPolicy);

        var metadata = Assert.Single(trainingRunsGateway.Items.Values);
        Assert.NotNull(metadata.EffectiveParameters);
        Assert.Equal(20, metadata.EffectiveParameters!.Epochs);
        Assert.Equal("all", metadata.EffectiveParameters.FineTuningPolicy);

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
            3,
            mlTrainingsGateway.LastRequest.ResolvedConfiguration.TrainingParameters.LrSchedulerPatience);
        Assert.Equal(
            0.5,
            mlTrainingsGateway.LastRequest.ResolvedConfiguration.TrainingParameters.LrSchedulerFactor);
        Assert.Equal(
            "all",
            mlTrainingsGateway.LastRequest.ResolvedConfiguration.TrainingParameters.FineTuningPolicy);
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

    private static CreateTrainingRunCommandHandler CreateHandler(
        InMemoryTrainingRunsGateway? trainingRunsGateway = null,
        StubMlTrainingsGateway? mlTrainingsGateway = null,
        StubModelsRegistryGateway? modelsRegistryGateway = null,
        StubProcessedDatasetsGateway? processedDatasetsGateway = null)
    {
        return new CreateTrainingRunCommandHandler(
            trainingRunsGateway ?? new InMemoryTrainingRunsGateway(),
            modelsRegistryGateway ?? new StubModelsRegistryGateway(CreateBaseModel(architectureFamily: "cnn")),
            processedDatasetsGateway ?? new StubProcessedDatasetsGateway(CreateProcessedDataset()),
            mlTrainingsGateway ?? new StubMlTrainingsGateway(),
            new StubTrainingEventsPathProvider(),
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
        int? LrSchedulerPatience = 3,
        double? LrSchedulerFactor = 0.5,
        string? FineTuningPolicy = "all")
    {
        return new TrainingRunRequestedParametersDto(
            Epochs: Epochs,
            LearningRate: LearningRate,
            BatchSize: BatchSize,
            EarlyStoppingPatience: EarlyStoppingPatience,
            LrSchedulerPatience: LrSchedulerPatience,
            LrSchedulerFactor: LrSchedulerFactor,
            FineTuningPolicy: FineTuningPolicy);
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
            FileName: "digits.npz",
            PreprocessingProfile: "default-28x28-v1",
            CreatedAtUtc: FixedNow.AddDays(-1),
            Sources: Array.Empty<SelectedRawDatasetSourceDto>(),
            SampleCounts: new SplitSampleCountsDto(Train: 10, Val: 4, Test: 2),
            SourceReports: Array.Empty<ProcessedDatasetSourceReportDto>(),
            Warnings: Array.Empty<string>());
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
        public StartMlTrainingRequestDto? LastRequest { get; private set; }

        public Task<StartMlTrainingResultDto> StartTrainingAsync(
            StartMlTrainingRequestDto request,
            CancellationToken cancellationToken = default)
        {
            LastRequest = request;
            return Task.FromResult(new StartMlTrainingResultDto(
                AcceptedAtUtc: FixedNow,
                MlJobId: "ml-job-01",
                Status: "queued"));
        }

        public Task<CancelMlTrainingResultDto> CancelTrainingAsync(
            CancelMlTrainingRequestDto request,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
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
