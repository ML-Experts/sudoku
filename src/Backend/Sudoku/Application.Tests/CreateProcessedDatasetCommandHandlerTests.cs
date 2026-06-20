using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Datasets;
using Sudoku.Application.Storage;

namespace Application.Tests;

public sealed class CreateProcessedDatasetCommandHandlerTests
{
    private static readonly DateTimeOffset FixedNow = DateTimeOffset.Parse("2026-06-20T00:15:00Z");

    [Fact]
    public async Task Handle_CreatesProcessedDatasetFromPreparation()
    {
        var preparationsGateway = new StubDatasetPreparationsGateway(
            new DatasetPreparationMetadataDto(
                PreparationName: "preparation-001",
                Status: "completed",
                CreatedAtUtc: FixedNow.AddHours(-1),
                Sources:
                [
                    new CreateDatasetPreparationSourceDto("v1_training", "board"),
                    new CreateDatasetPreparationSourceDto("mnist_train", "digit")
                ],
                SourceReports: [],
                Warnings: []));
        var artifactsGateway = new StubDatasetPreparationArtifactsGateway(
            boardSources: ["v1_training"],
            digitSources: ["mnist_train"]);
        var mlGateway = new StubMlDatasetsPreparationGateway(
            new PrepareDatasetArtifactResultDto(
                SampleCounts: new SplitSampleCountsDto(Train: 12, Val: 3, Test: 1),
                Sources:
                [
                    new PreparedDatasetSourceReportDto(
                        Name: "v1_training",
                        RequestedType: "board",
                        DetectedType: "board",
                        ProcessedSampleCount: 9,
                        IncludedSampleCount: 9,
                        EmptyCellCount: 0,
                        RejectedSampleCount: 0,
                        Warnings: []),
                    new PreparedDatasetSourceReportDto(
                        Name: "mnist_train",
                        RequestedType: "digit",
                        DetectedType: "digit",
                        ProcessedSampleCount: 7,
                        IncludedSampleCount: 7,
                        EmptyCellCount: 0,
                        RejectedSampleCount: 0,
                        Warnings: ["digit_warning"])
                ],
                Warnings: ["ml_warning"]));
        var processedDatasetsGateway = new StubProcessedDatasetsGateway();
        var handler = CreateHandler(
            preparationsGateway,
            artifactsGateway,
            mlGateway,
            processedDatasetsGateway);

        var result = await handler.Handle(
            new CreateProcessedDatasetCommand(
                PreparationName: " preparation-001 ",
                Name: " digits-v2 ",
                Sources:
                [
                    new SelectedRawDatasetSourceDto(" v1_training ", " BOARD ", ["mix"]),
                    new SelectedRawDatasetSourceDto(" mnist_train ", " digit ", ["train", "val"])
                ]),
            CancellationToken.None);

        Assert.Equal("digits-v2", result.Name);
        Assert.Equal("digits-v2.npz", result.FileName);
        Assert.Equal(FixedNow, result.CreatedAtUtc);
        Assert.Equal("preparation-001", mlGateway.LastRequest!.PreparationName);
        Assert.Equal("digits-v2", mlGateway.LastRequest.DatasetName);
        Assert.Equal("ratio", mlGateway.LastRequest.SplitPolicy.Mode);
        Assert.Equal("sourceType", mlGateway.LastRequest.SplitPolicy.GroupBy);
        Assert.Equal(0.8, mlGateway.LastRequest.SplitPolicy.Ratios.Train);
        Assert.Equal(0.1, mlGateway.LastRequest.SplitPolicy.Ratios.Val);
        Assert.Equal(0.1, mlGateway.LastRequest.SplitPolicy.Ratios.Test);
        Assert.Collection(
            mlGateway.LastRequest.Sources,
            source =>
            {
                Assert.Equal("v1_training", source.Name);
                Assert.Equal("board", source.Type);
                Assert.Equal(["mix"], source.Splits);
            },
            source =>
            {
                Assert.Equal("mnist_train", source.Name);
                Assert.Equal("digit", source.Type);
                Assert.Equal(["train", "val"], source.Splits);
            });

        Assert.Equal("digits-v2", processedDatasetsGateway.PromotedDatasetName);
        Assert.Equal("digits-v2.npz", processedDatasetsGateway.PromotedTargetFileName);
        Assert.NotNull(processedDatasetsGateway.SavedMetadata);
        Assert.Equal("preparation-001", processedDatasetsGateway.SavedMetadata!.PreparationName);
        Assert.Equal(["ml_warning"], processedDatasetsGateway.SavedMetadata.Warnings);
        Assert.Collection(
            processedDatasetsGateway.SavedMetadata.SourceReports,
            report => Assert.Equal("v1_training", report.Name),
            report => Assert.Equal("mnist_train", report.Name));
    }

    [Fact]
    public async Task Handle_ThrowsNotFound_WhenPreparationDoesNotExist()
    {
        var handler = CreateHandler(
            new StubDatasetPreparationsGateway(null),
            new StubDatasetPreparationArtifactsGateway(boardSources: [], digitSources: []),
            new StubMlDatasetsPreparationGateway(CreatePreparedArtifactResult()),
            new StubProcessedDatasetsGateway());

        await Assert.ThrowsAsync<DatasetPreparationNotFoundException>(() => handler.Handle(
            CreateCommand(),
            CancellationToken.None));
    }

    [Fact]
    public async Task Handle_ThrowsConflict_WhenPreparationArtifactsAreNotReady()
    {
        var handler = CreateHandler(
            new StubDatasetPreparationsGateway(new DatasetPreparationMetadataDto(
                PreparationName: "preparation-001",
                Status: "running",
                CreatedAtUtc: FixedNow.AddHours(-1),
                Sources: [],
                SourceReports: [],
                Warnings: [])),
            new StubDatasetPreparationArtifactsGateway(boardSources: ["v1_training"], digitSources: []),
            new StubMlDatasetsPreparationGateway(CreatePreparedArtifactResult()),
            new StubProcessedDatasetsGateway());

        var exception = await Assert.ThrowsAsync<DatasetPreparationArtifactsNotReadyException>(() => handler.Handle(
            CreateCommand(),
            CancellationToken.None));

        Assert.Equal("running", exception.Status);
    }

    [Fact]
    public async Task Handle_ThrowsNotFound_WhenSelectedSourceDoesNotExistInPreparation()
    {
        var handler = CreateHandler(
            new StubDatasetPreparationsGateway(new DatasetPreparationMetadataDto(
                PreparationName: "preparation-001",
                Status: "completed",
                CreatedAtUtc: FixedNow.AddHours(-1),
                Sources: [],
                SourceReports: [],
                Warnings: [])),
            new StubDatasetPreparationArtifactsGateway(boardSources: [], digitSources: []),
            new StubMlDatasetsPreparationGateway(CreatePreparedArtifactResult()),
            new StubProcessedDatasetsGateway());

        var exception = await Assert.ThrowsAsync<DatasetPreparationSourceNotFoundException>(() => handler.Handle(
            CreateCommand(),
            CancellationToken.None));

        Assert.Equal("v1_training", exception.SourceName);
    }

    private static CreateProcessedDatasetCommandHandler CreateHandler(
        IDatasetPreparationsGateway datasetPreparationsGateway,
        IDatasetPreparationArtifactsGateway datasetPreparationArtifactsGateway,
        IMlDatasetsPreparationGateway mlDatasetsPreparationGateway,
        IProcessedDatasetsGateway processedDatasetsGateway)
    {
        return new CreateProcessedDatasetCommandHandler(
            datasetPreparationsGateway,
            datasetPreparationArtifactsGateway,
            mlDatasetsPreparationGateway,
            processedDatasetsGateway,
            Options.Create(new DatasetsPreparationOptions
            {
                BoardsSubdirectory = "board",
                DigitsSubdirectory = "digit",
                PreparationsDirectoryPath = "/data/preparations",
                ProcessedDatasetsDirectoryPath = "/data/processed",
                TemporaryArtifactsDirectoryPath = "/data/tmp",
                DefaultPreprocessingProfile = "default-28x28-v1",
                DefaultMixSplitRatios = new DatasetsPreparationOptions.MixSplitRatiosOptions
                {
                    Train = 0.8,
                    Val = 0.1,
                    Test = 0.1
                }
            }),
            new FixedTimeProvider(FixedNow));
    }

    private static CreateProcessedDatasetCommand CreateCommand()
    {
        return new CreateProcessedDatasetCommand(
            PreparationName: "preparation-001",
            Name: "digits-v2",
            Sources:
            [
                new SelectedRawDatasetSourceDto("v1_training", "board", ["mix"])
            ]);
    }

    private static PrepareDatasetArtifactResultDto CreatePreparedArtifactResult()
    {
        return new PrepareDatasetArtifactResultDto(
            SampleCounts: new SplitSampleCountsDto(Train: 1, Val: 0, Test: 0),
            Sources:
            [
                new PreparedDatasetSourceReportDto(
                    Name: "v1_training",
                    RequestedType: "board",
                    DetectedType: "board",
                    ProcessedSampleCount: 1,
                    IncludedSampleCount: 1,
                    EmptyCellCount: 0,
                    RejectedSampleCount: 0,
                    Warnings: [])
            ],
            Warnings: []);
    }

    private sealed class StubDatasetPreparationsGateway : IDatasetPreparationsGateway
    {
        private readonly DatasetPreparationMetadataDto? _metadata;

        public StubDatasetPreparationsGateway(DatasetPreparationMetadataDto? metadata)
        {
            _metadata = metadata;
        }

        public Task<IReadOnlyList<DatasetPreparationMetadataDto>> ListAsync(CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task<DatasetPreparationMetadataDto?> GetByNameAsync(
            string preparationName,
            CancellationToken cancellationToken = default)
        {
            return Task.FromResult<DatasetPreparationMetadataDto?>(
                _metadata is not null && string.Equals(_metadata.PreparationName, preparationName, StringComparison.Ordinal)
                    ? _metadata
                    : null);
        }

        public Task<bool> TryCreateAsync(
            DatasetPreparationMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task UpdateAsync(
            DatasetPreparationMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task CleanupGeneratedContentAsync(
            string preparationName,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }
    }

    private sealed class StubDatasetPreparationArtifactsGateway : IDatasetPreparationArtifactsGateway
    {
        private readonly IReadOnlyList<string> _boardSources;
        private readonly IReadOnlyList<string> _digitSources;

        public StubDatasetPreparationArtifactsGateway(
            IReadOnlyList<string> boardSources,
            IReadOnlyList<string> digitSources)
        {
            _boardSources = boardSources;
            _digitSources = digitSources;
        }

        public Task<IReadOnlyList<string>> GetSourceFolderNamesAsync(
            string preparationName,
            string sourceType,
            CancellationToken cancellationToken = default)
        {
            var result = string.Equals(sourceType, "board", StringComparison.Ordinal)
                ? _boardSources
                : _digitSources;
            return Task.FromResult(result);
        }

        public Task<IReadOnlyList<string>> GetBoardFileNamesAsync(
            string preparationName,
            string sourceName,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task<Stream> OpenBoardArtifactReadAsync(
            string preparationName,
            string sourceName,
            string boardFolderName,
            string artifactFileName,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task ReplaceBoardFileNamesAsync(
            string preparationName,
            string sourceName,
            IReadOnlyList<string> boardFileNames,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task DeleteBoardDirectoryAsync(
            string preparationName,
            string sourceName,
            string boardFolderName,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }
    }

    private sealed class StubMlDatasetsPreparationGateway : IMlDatasetsPreparationGateway
    {
        private readonly PrepareDatasetArtifactResultDto _result;

        public StubMlDatasetsPreparationGateway(PrepareDatasetArtifactResultDto result)
        {
            _result = result;
        }

        public PrepareDatasetArtifactRequestDto? LastRequest { get; private set; }

        public Task<PrepareDatasetArtifactResultDto> PrepareDatasetArtifactAsync(
            PrepareDatasetArtifactRequestDto request,
            CancellationToken cancellationToken = default)
        {
            LastRequest = request;
            return Task.FromResult(_result);
        }
    }

    private sealed class StubProcessedDatasetsGateway : IProcessedDatasetsGateway
    {
        public string? PromotedDatasetName { get; private set; }

        public string? PromotedTargetFileName { get; private set; }

        public ProcessedDatasetMetadataDto? SavedMetadata { get; private set; }

        public Task<bool> IsProcessedDatasetNameAvailableAsync(
            string datasetName,
            CancellationToken cancellationToken = default)
        {
            return Task.FromResult(true);
        }

        public Task PromotePreparedArtifactAsync(
            string datasetName,
            string targetFileName,
            CancellationToken cancellationToken = default)
        {
            PromotedDatasetName = datasetName;
            PromotedTargetFileName = targetFileName;
            return Task.CompletedTask;
        }

        public Task SaveMetadataAsync(
            ProcessedDatasetMetadataDto metadata,
            CancellationToken cancellationToken = default)
        {
            SavedMetadata = metadata;
            return Task.CompletedTask;
        }

        public Task<IReadOnlyList<ProcessedDatasetMetadataDto>> ListAsync(CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
        }

        public Task<ProcessedDatasetMetadataDto?> GetByNameAsync(
            string datasetName,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
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
