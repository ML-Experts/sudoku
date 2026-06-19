using Sudoku.Application.Abstractions;
using Sudoku.Application.Datasets;

namespace Application.Tests;

public sealed class GetDatasetPreparationDetailsQueryHandlerTests
{
    [Fact]
    public async Task Handle_ReturnsPreparationDetailsMappedFromMetadata()
    {
        var metadata = CreateMetadata(
            preparationName: "preparation-001",
            createdAtUtc: DateTimeOffset.Parse("2026-06-19T18:42:11Z"),
            status: "completed",
            sources:
            [
                new CreateDatasetPreparationSourceDto("v1_training", "board"),
                new CreateDatasetPreparationSourceDto("mnist_train", "digit")
            ],
            sourceReports:
            [
                new DatasetPreparationSourceReportDto("mnist_train", "digit", 110, 3, 0),
                new DatasetPreparationSourceReportDto("v1_training", "board", 24, 2, 12)
            ],
            warnings: ["preparation_cleanup_partial"]);
        var handler = new GetDatasetPreparationDetailsQueryHandler(
            new StubDatasetPreparationsGateway(metadata));

        var result = await handler.Handle(
            new GetDatasetPreparationDetailsQuery("preparation-001"),
            CancellationToken.None);

        Assert.Equal("preparation-001", result.PreparationName);
        Assert.Equal("completed", result.Status);
        Assert.Collection(
            result.Sources,
            source =>
            {
                Assert.Equal("v1_training", source.Name);
                Assert.Equal("board", source.Type);
                Assert.Equal(24, source.PreparedItemsCount);
            },
            source =>
            {
                Assert.Equal("mnist_train", source.Name);
                Assert.Equal("digit", source.Type);
                Assert.Equal(110, source.PreparedItemsCount);
            });
        Assert.Equal(["preparation_cleanup_partial"], result.Warnings);
    }

    [Fact]
    public async Task Handle_UsesSelectedSourcesOrder_WhenSourceReportsAreMissingOrOutOfOrder()
    {
        var metadata = CreateMetadata(
            preparationName: "preparation-001",
            createdAtUtc: DateTimeOffset.Parse("2026-06-19T18:42:11Z"),
            status: "running",
            sources:
            [
                new CreateDatasetPreparationSourceDto("v1_training", "board"),
                new CreateDatasetPreparationSourceDto("mnist_train", "digit")
            ],
            sourceReports:
            [
                new DatasetPreparationSourceReportDto("mnist_train", "digit", 110, 0, 0)
            ],
            warnings: []);
        var handler = new GetDatasetPreparationDetailsQueryHandler(
            new StubDatasetPreparationsGateway(metadata));

        var result = await handler.Handle(
            new GetDatasetPreparationDetailsQuery("preparation-001"),
            CancellationToken.None);

        Assert.Collection(
            result.Sources,
            source =>
            {
                Assert.Equal("v1_training", source.Name);
                Assert.Equal("board", source.Type);
                Assert.Equal(0, source.PreparedItemsCount);
            },
            source =>
            {
                Assert.Equal("mnist_train", source.Name);
                Assert.Equal("digit", source.Type);
                Assert.Equal(110, source.PreparedItemsCount);
            });
    }

    [Fact]
    public async Task Handle_ReturnsEmptyWarnings_WhenMetadataWarningsAreNull()
    {
        var metadata = CreateMetadata(
            preparationName: "preparation-001",
            createdAtUtc: DateTimeOffset.Parse("2026-06-19T18:42:11Z"),
            status: "failed",
            sources:
            [
                new CreateDatasetPreparationSourceDto("v1_training", "board")
            ],
            sourceReports:
            [
                new DatasetPreparationSourceReportDto("v1_training", "board", 0, 5, 0)
            ],
            warnings: null);
        var handler = new GetDatasetPreparationDetailsQueryHandler(
            new StubDatasetPreparationsGateway(metadata));

        var result = await handler.Handle(
            new GetDatasetPreparationDetailsQuery("preparation-001"),
            CancellationToken.None);

        Assert.Equal("failed", result.Status);
        Assert.Empty(result.Warnings);
    }

    [Fact]
    public async Task Handle_ThrowsNotFound_WhenPreparationDoesNotExist()
    {
        var handler = new GetDatasetPreparationDetailsQueryHandler(
            new StubDatasetPreparationsGateway(metadata: null));

        await Assert.ThrowsAsync<DatasetPreparationNotFoundException>(() =>
            handler.Handle(new GetDatasetPreparationDetailsQuery("missing"), CancellationToken.None));
    }

    private static DatasetPreparationMetadataDto CreateMetadata(
        string preparationName,
        DateTimeOffset createdAtUtc,
        string status,
        IReadOnlyList<CreateDatasetPreparationSourceDto> sources,
        IReadOnlyList<DatasetPreparationSourceReportDto>? sourceReports,
        IReadOnlyList<string>? warnings)
    {
        return new DatasetPreparationMetadataDto(
            PreparationName: preparationName,
            Status: status,
            CreatedAtUtc: createdAtUtc,
            Sources: sources,
            SourceReports: sourceReports!,
            Warnings: warnings!,
            UpdatedAtUtc: createdAtUtc);
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
}
