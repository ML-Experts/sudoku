using Sudoku.Application.Abstractions;
using Sudoku.Application.Datasets;
using Sudoku.Models.Datasets;

namespace Application.Tests;

public sealed class GetDatasetPreparationBoardFilesQueryHandlerTests
{
    [Fact]
    public async Task Handle_ReturnsPaginatedBoardFiles_WhenPreparationIsCompletedAndSourceExists()
    {
        var metadata = CreateMetadata("preparation-001", DatasetPreparationStatus.Completed);
        var artifactsGateway = new StubDatasetPreparationArtifactsGateway(
            sourceFolderNames: ["v1_training", "v2_training"],
            boardFileNames: ["Image1", "Image2", "Image3"]);
        var handler = new GetDatasetPreparationBoardFilesQueryHandler(
            new StubDatasetPreparationsGateway(metadata),
            artifactsGateway);

        var result = await handler.Handle(
            new GetDatasetPreparationBoardFilesQuery("preparation-001", "v1_training", 2, 2),
            CancellationToken.None);

        Assert.Equal("preparation-001", result.PreparationName);
        Assert.Equal("v1_training", result.SourceName);
        Assert.Equal(2, result.Page);
        Assert.Equal(2, result.PageSize);
        Assert.Equal(3, result.TotalCount);
        Assert.Collection(
            result.Items,
            item => Assert.Equal("Image3", item.BoardFolderName));
        Assert.Equal("preparation-001", artifactsGateway.LastPreparationNameForSources);
        Assert.Equal("board", artifactsGateway.LastSourceType);
        Assert.Equal("preparation-001", artifactsGateway.LastPreparationNameForBoardFiles);
        Assert.Equal("v1_training", artifactsGateway.LastSourceNameForBoardFiles);
    }

    [Fact]
    public async Task Handle_ReturnsEmptyItems_WhenBoardManifestIsEmpty()
    {
        var handler = new GetDatasetPreparationBoardFilesQueryHandler(
            new StubDatasetPreparationsGateway(CreateMetadata("preparation-001", DatasetPreparationStatus.Completed)),
            new StubDatasetPreparationArtifactsGateway(
                sourceFolderNames: ["v1_training"],
                boardFileNames: []));

        var result = await handler.Handle(
            new GetDatasetPreparationBoardFilesQuery("preparation-001", "v1_training", 1, 50),
            CancellationToken.None);

        Assert.Empty(result.Items);
        Assert.Equal(0, result.TotalCount);
    }

    [Fact]
    public async Task Handle_ReturnsEmptyItems_WhenRequestedPageIsOutsideAvailableRange()
    {
        var handler = new GetDatasetPreparationBoardFilesQueryHandler(
            new StubDatasetPreparationsGateway(CreateMetadata("preparation-001", DatasetPreparationStatus.Completed)),
            new StubDatasetPreparationArtifactsGateway(
                sourceFolderNames: ["v1_training"],
                boardFileNames: ["Image1", "Image2"]));

        var result = await handler.Handle(
            new GetDatasetPreparationBoardFilesQuery("preparation-001", "v1_training", 3, 2),
            CancellationToken.None);

        Assert.Empty(result.Items);
        Assert.Equal(2, result.TotalCount);
    }

    [Fact]
    public async Task Handle_ThrowsNotFound_WhenPreparationDoesNotExist()
    {
        var handler = new GetDatasetPreparationBoardFilesQueryHandler(
            new StubDatasetPreparationsGateway(metadata: null),
            new StubDatasetPreparationArtifactsGateway(
                sourceFolderNames: ["v1_training"],
                boardFileNames: ["Image1"]));

        await Assert.ThrowsAsync<DatasetPreparationNotFoundException>(() =>
            handler.Handle(
                new GetDatasetPreparationBoardFilesQuery("missing", "v1_training", 1, 50),
                CancellationToken.None));
    }

    [Theory]
    [InlineData(DatasetPreparationStatus.Queued)]
    [InlineData(DatasetPreparationStatus.Running)]
    [InlineData(DatasetPreparationStatus.Failed)]
    public async Task Handle_ThrowsConflict_WhenPreparationArtifactsAreNotReady(string status)
    {
        var handler = new GetDatasetPreparationBoardFilesQueryHandler(
            new StubDatasetPreparationsGateway(CreateMetadata("preparation-001", status)),
            new StubDatasetPreparationArtifactsGateway(
                sourceFolderNames: ["v1_training"],
                boardFileNames: ["Image1"]));

        var exception = await Assert.ThrowsAsync<DatasetPreparationArtifactsNotReadyException>(() =>
            handler.Handle(
                new GetDatasetPreparationBoardFilesQuery("preparation-001", "v1_training", 1, 50),
                CancellationToken.None));

        Assert.Equal("preparation-001", exception.PreparationName);
        Assert.Equal(status, exception.Status);
    }

    [Fact]
    public async Task Handle_ThrowsNotFound_WhenBoardSourceDoesNotExist()
    {
        var handler = new GetDatasetPreparationBoardFilesQueryHandler(
            new StubDatasetPreparationsGateway(CreateMetadata("preparation-001", DatasetPreparationStatus.Completed)),
            new StubDatasetPreparationArtifactsGateway(
                sourceFolderNames: ["v2_training"],
                boardFileNames: ["Image1"]));

        var exception = await Assert.ThrowsAsync<DatasetPreparationSourceNotFoundException>(() =>
            handler.Handle(
                new GetDatasetPreparationBoardFilesQuery("preparation-001", "v1_training", 1, 50),
                CancellationToken.None));

        Assert.Equal("preparation-001", exception.PreparationName);
        Assert.Equal("v1_training", exception.SourceName);
    }

    private static DatasetPreparationMetadataDto CreateMetadata(string preparationName, string status)
    {
        return new DatasetPreparationMetadataDto(
            PreparationName: preparationName,
            Status: status,
            CreatedAtUtc: DateTimeOffset.Parse("2026-06-19T18:42:11Z"),
            Sources:
            [
                new CreateDatasetPreparationSourceDto("v1_training", "board")
            ],
            SourceReports:
            [
                new DatasetPreparationSourceReportDto("v1_training", "board", 24, 0, 0)
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
            return Task.FromResult(_metadata);
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
        private readonly IReadOnlyList<string> _sourceFolderNames;
        private readonly IReadOnlyList<string> _boardFileNames;

        public StubDatasetPreparationArtifactsGateway(
            IReadOnlyList<string> sourceFolderNames,
            IReadOnlyList<string> boardFileNames)
        {
            _sourceFolderNames = sourceFolderNames;
            _boardFileNames = boardFileNames;
        }

        public string? LastPreparationNameForSources { get; private set; }

        public string? LastSourceType { get; private set; }

        public string? LastPreparationNameForBoardFiles { get; private set; }

        public string? LastSourceNameForBoardFiles { get; private set; }

        public Task<IReadOnlyList<string>> GetSourceFolderNamesAsync(
            string preparationName,
            string sourceType,
            CancellationToken cancellationToken = default)
        {
            LastPreparationNameForSources = preparationName;
            LastSourceType = sourceType;
            return Task.FromResult(_sourceFolderNames);
        }

        public Task<IReadOnlyList<string>> GetBoardFileNamesAsync(
            string preparationName,
            string sourceName,
            CancellationToken cancellationToken = default)
        {
            LastPreparationNameForBoardFiles = preparationName;
            LastSourceNameForBoardFiles = sourceName;
            return Task.FromResult(_boardFileNames);
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
}
