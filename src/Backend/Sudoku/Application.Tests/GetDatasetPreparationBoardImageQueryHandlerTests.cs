using Sudoku.Application.Abstractions;
using Sudoku.Application.Datasets;
using Sudoku.Application.Storage;
using Sudoku.Models.Datasets;

namespace Application.Tests;

public sealed class GetDatasetPreparationBoardImageQueryHandlerTests
{
    [Fact]
    public async Task Handle_ReturnsImageAsBase64_WhenPreparationIsCompletedAndBoardExists()
    {
        var metadata = CreateMetadata("preparation-001", DatasetPreparationStatus.Completed);
        var artifactsGateway = new StubDatasetPreparationArtifactsGateway(
            sourceFolderNames: ["v1_training"],
            boardFileNames: ["Image1"],
            artifactBytes: [0x01, 0x02, 0x03, 0x04]);
        var handler = new GetDatasetPreparationBoardImageQueryHandler(
            new StubDatasetPreparationsGateway(metadata),
            artifactsGateway);

        var result = await handler.Handle(
            new GetDatasetPreparationBoardImageQuery("preparation-001", "v1_training", "Image1"),
            CancellationToken.None);

        Assert.Equal("image/png", result.MimeType);
        Assert.Equal(Convert.ToBase64String([0x01, 0x02, 0x03, 0x04]), result.Base64);
        Assert.Equal("preparation-001", artifactsGateway.LastPreparationNameForSources);
        Assert.Equal("board", artifactsGateway.LastSourceType);
        Assert.Equal("preparation-001", artifactsGateway.LastPreparationNameForBoardFiles);
        Assert.Equal("v1_training", artifactsGateway.LastSourceNameForBoardFiles);
        Assert.Equal("preparation-001", artifactsGateway.LastPreparationNameForArtifact);
        Assert.Equal("v1_training", artifactsGateway.LastSourceNameForArtifact);
        Assert.Equal("Image1", artifactsGateway.LastBoardFolderNameForArtifact);
        Assert.Equal(DatasetPreparationBoardArtifactNames.CorrectedBoardFileName, artifactsGateway.LastArtifactFileName);
    }

    [Fact]
    public async Task Handle_ThrowsNotFound_WhenPreparationDoesNotExist()
    {
        var handler = new GetDatasetPreparationBoardImageQueryHandler(
            new StubDatasetPreparationsGateway(metadata: null),
            new StubDatasetPreparationArtifactsGateway(
                sourceFolderNames: ["v1_training"],
                boardFileNames: ["Image1"],
                artifactBytes: [0x01]));

        await Assert.ThrowsAsync<DatasetPreparationNotFoundException>(() =>
            handler.Handle(
                new GetDatasetPreparationBoardImageQuery("missing", "v1_training", "Image1"),
                CancellationToken.None));
    }

    [Theory]
    [InlineData(DatasetPreparationStatus.Queued)]
    [InlineData(DatasetPreparationStatus.Running)]
    [InlineData(DatasetPreparationStatus.Failed)]
    public async Task Handle_ThrowsConflict_WhenPreparationArtifactsAreNotReady(string status)
    {
        var handler = new GetDatasetPreparationBoardImageQueryHandler(
            new StubDatasetPreparationsGateway(CreateMetadata("preparation-001", status)),
            new StubDatasetPreparationArtifactsGateway(
                sourceFolderNames: ["v1_training"],
                boardFileNames: ["Image1"],
                artifactBytes: [0x01]));

        var exception = await Assert.ThrowsAsync<DatasetPreparationArtifactsNotReadyException>(() =>
            handler.Handle(
                new GetDatasetPreparationBoardImageQuery("preparation-001", "v1_training", "Image1"),
                CancellationToken.None));

        Assert.Equal("preparation-001", exception.PreparationName);
        Assert.Equal(status, exception.Status);
    }

    [Fact]
    public async Task Handle_ThrowsNotFound_WhenBoardSourceDoesNotExist()
    {
        var handler = new GetDatasetPreparationBoardImageQueryHandler(
            new StubDatasetPreparationsGateway(CreateMetadata("preparation-001", DatasetPreparationStatus.Completed)),
            new StubDatasetPreparationArtifactsGateway(
                sourceFolderNames: ["v2_training"],
                boardFileNames: ["Image1"],
                artifactBytes: [0x01]));

        var exception = await Assert.ThrowsAsync<DatasetPreparationSourceNotFoundException>(() =>
            handler.Handle(
                new GetDatasetPreparationBoardImageQuery("preparation-001", "v1_training", "Image1"),
                CancellationToken.None));

        Assert.Equal("preparation-001", exception.PreparationName);
        Assert.Equal("v1_training", exception.SourceName);
    }

    [Fact]
    public async Task Handle_ThrowsNotFound_WhenBoardFolderDoesNotExistInManifest()
    {
        var handler = new GetDatasetPreparationBoardImageQueryHandler(
            new StubDatasetPreparationsGateway(CreateMetadata("preparation-001", DatasetPreparationStatus.Completed)),
            new StubDatasetPreparationArtifactsGateway(
                sourceFolderNames: ["v1_training"],
                boardFileNames: ["Image2"],
                artifactBytes: [0x01]));

        var exception = await Assert.ThrowsAsync<DatasetPreparationBoardFileNotFoundException>(() =>
            handler.Handle(
                new GetDatasetPreparationBoardImageQuery("preparation-001", "v1_training", "Image1"),
                CancellationToken.None));

        Assert.Equal("preparation-001", exception.PreparationName);
        Assert.Equal("v1_training", exception.SourceName);
        Assert.Equal("Image1", exception.BoardFolderName);
    }

    [Fact]
    public async Task Handle_PropagatesTechnicalFailure_WhenArtifactIsMissingForManifestEntry()
    {
        var handler = new GetDatasetPreparationBoardImageQueryHandler(
            new StubDatasetPreparationsGateway(CreateMetadata("preparation-001", DatasetPreparationStatus.Completed)),
            new StubDatasetPreparationArtifactsGateway(
                sourceFolderNames: ["v1_training"],
                boardFileNames: ["Image1"],
                artifactOpenException: new FileStorageItemNotFoundException("Wskazany plik nie istnieje.")));

        await Assert.ThrowsAsync<FileStorageItemNotFoundException>(() =>
            handler.Handle(
                new GetDatasetPreparationBoardImageQuery("preparation-001", "v1_training", "Image1"),
                CancellationToken.None));
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
        private readonly byte[]? _artifactBytes;
        private readonly Exception? _artifactOpenException;

        public StubDatasetPreparationArtifactsGateway(
            IReadOnlyList<string> sourceFolderNames,
            IReadOnlyList<string> boardFileNames,
            byte[]? artifactBytes = null,
            Exception? artifactOpenException = null)
        {
            _sourceFolderNames = sourceFolderNames;
            _boardFileNames = boardFileNames;
            _artifactBytes = artifactBytes;
            _artifactOpenException = artifactOpenException;
        }

        public string? LastPreparationNameForSources { get; private set; }

        public string? LastSourceType { get; private set; }

        public string? LastPreparationNameForBoardFiles { get; private set; }

        public string? LastSourceNameForBoardFiles { get; private set; }

        public string? LastPreparationNameForArtifact { get; private set; }

        public string? LastSourceNameForArtifact { get; private set; }

        public string? LastBoardFolderNameForArtifact { get; private set; }

        public string? LastArtifactFileName { get; private set; }

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
            LastPreparationNameForArtifact = preparationName;
            LastSourceNameForArtifact = sourceName;
            LastBoardFolderNameForArtifact = boardFolderName;
            LastArtifactFileName = artifactFileName;

            if (_artifactOpenException is not null)
            {
                throw _artifactOpenException;
            }

            Stream stream = new MemoryStream(_artifactBytes ?? []);
            return Task.FromResult(stream);
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
