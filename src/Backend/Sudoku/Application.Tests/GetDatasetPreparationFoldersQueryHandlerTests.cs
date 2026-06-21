using Sudoku.Application.Abstractions;
using Sudoku.Application.Datasets;
using Sudoku.Models.Datasets;

namespace Application.Tests;

public sealed class GetDatasetPreparationFoldersQueryHandlerTests
{
    [Fact]
    public async Task Handle_ReturnsFoldersFromManifest_WhenPreparationIsCompleted()
    {
        var metadata = CreateMetadata("preparation-001", DatasetPreparationStatus.Completed);
        var artifactsGateway = new StubDatasetPreparationArtifactsGateway(["v2_training", "v1_training"]);
        var handler = new GetDatasetPreparationFoldersQueryHandler(
            new StubDatasetPreparationsGateway(metadata),
            artifactsGateway);

        var result = await handler.Handle(
            new GetDatasetPreparationFoldersQuery("preparation-001", "board"),
            CancellationToken.None);

        Assert.Equal("preparation-001", result.PreparationName);
        Assert.Equal("board", result.Type);
        Assert.Equal(2, result.TotalCount);
        Assert.Equal(["v2_training", "v1_training"], result.Items);
        Assert.Equal("preparation-001", artifactsGateway.LastPreparationName);
        Assert.Equal("board", artifactsGateway.LastSourceType);
    }

    [Fact]
    public async Task Handle_ReturnsEmptyItems_WhenManifestIsEmpty()
    {
        var handler = new GetDatasetPreparationFoldersQueryHandler(
            new StubDatasetPreparationsGateway(CreateMetadata("preparation-001", DatasetPreparationStatus.Completed)),
            new StubDatasetPreparationArtifactsGateway([]));

        var result = await handler.Handle(
            new GetDatasetPreparationFoldersQuery("preparation-001", "board"),
            CancellationToken.None);

        Assert.Empty(result.Items);
        Assert.Equal(0, result.TotalCount);
    }

    [Fact]
    public async Task Handle_PassesDigitTypeToArtifactsGateway_WhenDigitFoldersAreRequested()
    {
        var metadata = CreateMetadata("preparation-001", DatasetPreparationStatus.Completed);
        var artifactsGateway = new StubDatasetPreparationArtifactsGateway(["mnist_train", "mnist_test"]);
        var handler = new GetDatasetPreparationFoldersQueryHandler(
            new StubDatasetPreparationsGateway(metadata),
            artifactsGateway);

        var result = await handler.Handle(
            new GetDatasetPreparationFoldersQuery("preparation-001", "digit"),
            CancellationToken.None);

        Assert.Equal("preparation-001", result.PreparationName);
        Assert.Equal("digit", result.Type);
        Assert.Equal(2, result.TotalCount);
        Assert.Equal(["mnist_train", "mnist_test"], result.Items);
        Assert.Equal("preparation-001", artifactsGateway.LastPreparationName);
        Assert.Equal("digit", artifactsGateway.LastSourceType);
    }

    [Fact]
    public async Task Handle_ThrowsNotFound_WhenPreparationDoesNotExist()
    {
        var handler = new GetDatasetPreparationFoldersQueryHandler(
            new StubDatasetPreparationsGateway(metadata: null),
            new StubDatasetPreparationArtifactsGateway(["v1_training"]));

        await Assert.ThrowsAsync<DatasetPreparationNotFoundException>(() =>
            handler.Handle(new GetDatasetPreparationFoldersQuery("missing", "board"), CancellationToken.None));
    }

    [Theory]
    [InlineData(DatasetPreparationStatus.Queued)]
    [InlineData(DatasetPreparationStatus.Running)]
    [InlineData(DatasetPreparationStatus.Failed)]
    public async Task Handle_ThrowsConflict_WhenPreparationArtifactsAreNotReady(string status)
    {
        var handler = new GetDatasetPreparationFoldersQueryHandler(
            new StubDatasetPreparationsGateway(CreateMetadata("preparation-001", status)),
            new StubDatasetPreparationArtifactsGateway(["v1_training"]));

        var exception = await Assert.ThrowsAsync<DatasetPreparationArtifactsNotReadyException>(() =>
            handler.Handle(new GetDatasetPreparationFoldersQuery("preparation-001", "board"), CancellationToken.None));

        Assert.Equal("preparation-001", exception.PreparationName);
        Assert.Equal(status, exception.Status);
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
        private readonly IReadOnlyList<string> _items;

        public StubDatasetPreparationArtifactsGateway(IReadOnlyList<string> items)
        {
            _items = items;
        }

        public string? LastPreparationName { get; private set; }

        public string? LastSourceType { get; private set; }

        public Task<IReadOnlyList<string>> GetSourceFolderNamesAsync(
            string preparationName,
            string sourceType,
            CancellationToken cancellationToken = default)
        {
            LastPreparationName = preparationName;
            LastSourceType = sourceType;
            return Task.FromResult(_items);
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
}
