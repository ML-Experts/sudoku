using Sudoku.Application.Abstractions;
using Sudoku.Application.Datasets;
using Sudoku.Models.Datasets;

namespace Application.Tests;

public sealed class DeleteDatasetPreparationBoardFileCommandHandlerTests
{
    [Fact]
    public async Task Handle_DeletesBoardAndUpdatesManifest_WhenRequestIsValid()
    {
        var metadata = CreateMetadata("preparation-001", DatasetPreparationStatus.Completed);
        var artifactsGateway = new StubDatasetPreparationArtifactsGateway(
            sourceFolderNames: ["v1_training"],
            boardFileNames: ["Image1", "Image2", "Image3"]);
        var handler = CreateHandler(metadata, artifactsGateway);

        var result = await handler.Handle(
            new DeleteDatasetPreparationBoardFileCommand("preparation-001", "v1_training", "Image2"),
            CancellationToken.None);

        Assert.Equal("preparation-001", result.PreparationName);
        Assert.Equal("v1_training", result.SourceName);
        Assert.Equal("Image2", result.BoardFolderName);
        Assert.True(result.Deleted);
        Assert.Equal(2, result.RemainingItemsCount);
        Assert.Equal("preparation-001", artifactsGateway.LastPreparationNameForSources);
        Assert.Equal("board", artifactsGateway.LastSourceType);
        Assert.Equal("preparation-001", artifactsGateway.LastPreparationNameForBoardFiles);
        Assert.Equal("v1_training", artifactsGateway.LastSourceNameForBoardFiles);
        Assert.Equal("preparation-001", artifactsGateway.LastPreparationNameForManifestReplace);
        Assert.Equal("v1_training", artifactsGateway.LastSourceNameForManifestReplace);
        Assert.Equal(["Image1", "Image3"], artifactsGateway.ReplacedBoardFileNames);
        Assert.Equal("preparation-001", artifactsGateway.LastPreparationNameForDeletedBoardDirectory);
        Assert.Equal("v1_training", artifactsGateway.LastSourceNameForDeletedBoardDirectory);
        Assert.Equal("Image2", artifactsGateway.LastDeletedBoardFolderName);
        Assert.Equal(1, artifactsGateway.ReplaceBoardFileNamesCallCount);
        Assert.Equal(1, artifactsGateway.DeleteBoardDirectoryCallCount);
    }

    [Fact]
    public async Task Handle_AllowsDeletingLastBoardEntry_AndPersistsEmptyManifest()
    {
        var handler = CreateHandler(
            CreateMetadata("preparation-001", DatasetPreparationStatus.Completed),
            new StubDatasetPreparationArtifactsGateway(
                sourceFolderNames: ["v1_training"],
                boardFileNames: ["Image1"]));

        var result = await handler.Handle(
            new DeleteDatasetPreparationBoardFileCommand("preparation-001", "v1_training", "Image1"),
            CancellationToken.None);

        Assert.True(result.Deleted);
        Assert.Equal(0, result.RemainingItemsCount);
    }

    [Fact]
    public async Task Handle_ThrowsNotFound_WhenPreparationDoesNotExist()
    {
        var handler = CreateHandler(
            metadata: null,
            new StubDatasetPreparationArtifactsGateway(
                sourceFolderNames: ["v1_training"],
                boardFileNames: ["Image1"]));

        await Assert.ThrowsAsync<DatasetPreparationNotFoundException>(() =>
            handler.Handle(
                new DeleteDatasetPreparationBoardFileCommand("missing", "v1_training", "Image1"),
                CancellationToken.None));
    }

    [Theory]
    [InlineData(DatasetPreparationStatus.Queued)]
    [InlineData(DatasetPreparationStatus.Running)]
    [InlineData(DatasetPreparationStatus.Failed)]
    public async Task Handle_ThrowsConflict_WhenPreparationArtifactsAreNotReady(string status)
    {
        var handler = CreateHandler(
            CreateMetadata("preparation-001", status),
            new StubDatasetPreparationArtifactsGateway(
                sourceFolderNames: ["v1_training"],
                boardFileNames: ["Image1"]));

        var exception = await Assert.ThrowsAsync<DatasetPreparationArtifactsNotReadyException>(() =>
            handler.Handle(
                new DeleteDatasetPreparationBoardFileCommand("preparation-001", "v1_training", "Image1"),
                CancellationToken.None));

        Assert.Equal("preparation-001", exception.PreparationName);
        Assert.Equal(status, exception.Status);
    }

    [Fact]
    public async Task Handle_ThrowsNotFound_WhenBoardSourceDoesNotExist()
    {
        var handler = CreateHandler(
            CreateMetadata("preparation-001", DatasetPreparationStatus.Completed),
            new StubDatasetPreparationArtifactsGateway(
                sourceFolderNames: ["v2_training"],
                boardFileNames: ["Image1"]));

        var exception = await Assert.ThrowsAsync<DatasetPreparationSourceNotFoundException>(() =>
            handler.Handle(
                new DeleteDatasetPreparationBoardFileCommand("preparation-001", "v1_training", "Image1"),
                CancellationToken.None));

        Assert.Equal("preparation-001", exception.PreparationName);
        Assert.Equal("v1_training", exception.SourceName);
    }

    [Fact]
    public async Task Handle_ThrowsNotFound_WhenBoardFolderDoesNotExistInManifest()
    {
        var handler = CreateHandler(
            CreateMetadata("preparation-001", DatasetPreparationStatus.Completed),
            new StubDatasetPreparationArtifactsGateway(
                sourceFolderNames: ["v1_training"],
                boardFileNames: ["Image2"]));

        var exception = await Assert.ThrowsAsync<DatasetPreparationBoardFileNotFoundException>(() =>
            handler.Handle(
                new DeleteDatasetPreparationBoardFileCommand("preparation-001", "v1_training", "Image1"),
                CancellationToken.None));

        Assert.Equal("preparation-001", exception.PreparationName);
        Assert.Equal("v1_training", exception.SourceName);
        Assert.Equal("Image1", exception.BoardFolderName);
    }

    [Fact]
    public async Task Handle_PropagatesManifestWriteFailure_WithoutDeletingDirectory()
    {
        var artifactsGateway = new StubDatasetPreparationArtifactsGateway(
            sourceFolderNames: ["v1_training"],
            boardFileNames: ["Image1", "Image2"],
            replaceBoardFileNamesException: new IOException("manifest write failed"));
        var handler = CreateHandler(
            CreateMetadata("preparation-001", DatasetPreparationStatus.Completed),
            artifactsGateway);

        await Assert.ThrowsAsync<IOException>(() =>
            handler.Handle(
                new DeleteDatasetPreparationBoardFileCommand("preparation-001", "v1_training", "Image1"),
                CancellationToken.None));

        Assert.Equal(1, artifactsGateway.ReplaceBoardFileNamesCallCount);
        Assert.Equal(0, artifactsGateway.DeleteBoardDirectoryCallCount);
    }

    [Fact]
    public async Task Handle_RollsBackManifest_WhenDirectoryDeleteFails()
    {
        var artifactsGateway = new StubDatasetPreparationArtifactsGateway(
            sourceFolderNames: ["v1_training"],
            boardFileNames: ["Image1", "Image2"],
            deleteBoardDirectoryException: new IOException("delete failed"));
        var handler = CreateHandler(
            CreateMetadata("preparation-001", DatasetPreparationStatus.Completed),
            artifactsGateway);

        await Assert.ThrowsAsync<IOException>(() =>
            handler.Handle(
                new DeleteDatasetPreparationBoardFileCommand("preparation-001", "v1_training", "Image1"),
                CancellationToken.None));

        Assert.Equal(2, artifactsGateway.ReplaceBoardFileNamesCallCount);
        Assert.Equal(["Image1", "Image2"], artifactsGateway.ReplacedBoardFileNamesHistory[1]);
        Assert.Equal(1, artifactsGateway.DeleteBoardDirectoryCallCount);
    }

    [Fact]
    public async Task Handle_StillPropagatesDeleteFailure_WhenRollbackAlsoFails()
    {
        var artifactsGateway = new StubDatasetPreparationArtifactsGateway(
            sourceFolderNames: ["v1_training"],
            boardFileNames: ["Image1", "Image2"],
            deleteBoardDirectoryException: new IOException("delete failed"),
            replaceBoardFileNamesExceptionSequence:
            [
                null,
                new UnauthorizedAccessException("rollback failed")
            ]);
        var handler = CreateHandler(
            CreateMetadata("preparation-001", DatasetPreparationStatus.Completed),
            artifactsGateway);

        var exception = await Assert.ThrowsAsync<IOException>(() =>
            handler.Handle(
                new DeleteDatasetPreparationBoardFileCommand("preparation-001", "v1_training", "Image1"),
                CancellationToken.None));

        Assert.Equal("delete failed", exception.Message);
        Assert.Equal(2, artifactsGateway.ReplaceBoardFileNamesCallCount);
        Assert.Equal(1, artifactsGateway.DeleteBoardDirectoryCallCount);
    }

    private static DeleteDatasetPreparationBoardFileCommandHandler CreateHandler(
        DatasetPreparationMetadataDto? metadata,
        StubDatasetPreparationArtifactsGateway artifactsGateway)
    {
        return new DeleteDatasetPreparationBoardFileCommandHandler(
            new StubDatasetPreparationsGateway(metadata),
            artifactsGateway);
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
        private readonly Exception? _replaceBoardFileNamesException;
        private readonly Queue<Exception?> _replaceBoardFileNamesExceptionSequence;
        private readonly Exception? _deleteBoardDirectoryException;

        public StubDatasetPreparationArtifactsGateway(
            IReadOnlyList<string> sourceFolderNames,
            IReadOnlyList<string> boardFileNames,
            Exception? replaceBoardFileNamesException = null,
            Exception? deleteBoardDirectoryException = null,
            IReadOnlyList<Exception?>? replaceBoardFileNamesExceptionSequence = null)
        {
            _sourceFolderNames = sourceFolderNames;
            _boardFileNames = boardFileNames;
            _replaceBoardFileNamesException = replaceBoardFileNamesException;
            _deleteBoardDirectoryException = deleteBoardDirectoryException;
            _replaceBoardFileNamesExceptionSequence = new Queue<Exception?>(
                replaceBoardFileNamesExceptionSequence ?? Array.Empty<Exception?>());
        }

        public string? LastPreparationNameForSources { get; private set; }

        public string? LastSourceType { get; private set; }

        public string? LastPreparationNameForBoardFiles { get; private set; }

        public string? LastSourceNameForBoardFiles { get; private set; }

        public string? LastPreparationNameForManifestReplace { get; private set; }

        public string? LastSourceNameForManifestReplace { get; private set; }

        public IReadOnlyList<string>? ReplacedBoardFileNames { get; private set; }

        public List<IReadOnlyList<string>> ReplacedBoardFileNamesHistory { get; } = [];

        public int ReplaceBoardFileNamesCallCount { get; private set; }

        public string? LastPreparationNameForDeletedBoardDirectory { get; private set; }

        public string? LastSourceNameForDeletedBoardDirectory { get; private set; }

        public string? LastDeletedBoardFolderName { get; private set; }

        public int DeleteBoardDirectoryCallCount { get; private set; }

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
            ReplaceBoardFileNamesCallCount++;
            LastPreparationNameForManifestReplace = preparationName;
            LastSourceNameForManifestReplace = sourceName;
            ReplacedBoardFileNames = boardFileNames.ToArray();
            ReplacedBoardFileNamesHistory.Add(boardFileNames.ToArray());

            if (_replaceBoardFileNamesExceptionSequence.Count > 0)
            {
                var exception = _replaceBoardFileNamesExceptionSequence.Dequeue();
                if (exception is not null)
                {
                    throw exception;
                }
            }
            else if (_replaceBoardFileNamesException is not null)
            {
                throw _replaceBoardFileNamesException;
            }

            return Task.CompletedTask;
        }

        public Task DeleteBoardDirectoryAsync(
            string preparationName,
            string sourceName,
            string boardFolderName,
            CancellationToken cancellationToken = default)
        {
            DeleteBoardDirectoryCallCount++;
            LastPreparationNameForDeletedBoardDirectory = preparationName;
            LastSourceNameForDeletedBoardDirectory = sourceName;
            LastDeletedBoardFolderName = boardFolderName;

            if (_deleteBoardDirectoryException is not null)
            {
                throw _deleteBoardDirectoryException;
            }

            return Task.CompletedTask;
        }
    }
}
