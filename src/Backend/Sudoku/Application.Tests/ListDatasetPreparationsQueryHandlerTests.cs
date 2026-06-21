using Sudoku.Application.Abstractions;
using Sudoku.Application.Datasets;

namespace Application.Tests;

public sealed class ListDatasetPreparationsQueryHandlerTests
{
    [Fact]
    public async Task Handle_ReturnsEmptyList_WhenNoPreparationsExist()
    {
        var handler = new ListDatasetPreparationsQueryHandler(new InMemoryDatasetPreparationsGateway());

        var result = await handler.Handle(new ListDatasetPreparationsQuery(), CancellationToken.None);

        Assert.Empty(result.Items);
        Assert.Equal(0, result.TotalCount);
    }

    [Fact]
    public async Task Handle_SortsPreparationsDescendingByCreatedAtUtc()
    {
        var handler = new ListDatasetPreparationsQueryHandler(new InMemoryDatasetPreparationsGateway(
        [
            CreateMetadata("older", DateTimeOffset.Parse("2026-06-19T18:42:11Z"), [new CreateDatasetPreparationSourceDto("v1", "board")]),
            CreateMetadata("newer", DateTimeOffset.Parse("2026-06-19T19:05:44Z"), [new CreateDatasetPreparationSourceDto("mnist", "digit")])
        ]));

        var result = await handler.Handle(new ListDatasetPreparationsQuery(), CancellationToken.None);

        Assert.Equal(2, result.TotalCount);
        Assert.Collection(
            result.Items,
            item => Assert.Equal("newer", item.PreparationName),
            item => Assert.Equal("older", item.PreparationName));
    }

    [Fact]
    public async Task Handle_CountsBoardAndDigitSourcesFromMetadataSources()
    {
        var handler = new ListDatasetPreparationsQueryHandler(new InMemoryDatasetPreparationsGateway(
        [
            CreateMetadata(
                "preparation-001",
                DateTimeOffset.Parse("2026-06-19T18:42:11Z"),
                [
                    new CreateDatasetPreparationSourceDto("v1_training", "board"),
                    new CreateDatasetPreparationSourceDto("v2_training", "board"),
                    new CreateDatasetPreparationSourceDto("mnist_train", "digit")
                ],
                sourceReports: [])
        ]));

        var result = await handler.Handle(new ListDatasetPreparationsQuery(), CancellationToken.None);

        var item = Assert.Single(result.Items);
        Assert.Equal(2, item.BoardSourcesCount);
        Assert.Equal(1, item.DigitSourcesCount);
    }

    [Fact]
    public async Task Handle_UsesSelectedSourcesCounts_WhenSourceReportsAreEmpty()
    {
        var handler = new ListDatasetPreparationsQueryHandler(new InMemoryDatasetPreparationsGateway(
        [
            CreateMetadata(
                "preparation-001",
                DateTimeOffset.Parse("2026-06-19T18:42:11Z"),
                [
                    new CreateDatasetPreparationSourceDto("v1_training", "board"),
                    new CreateDatasetPreparationSourceDto("mnist_train", "digit")
                ],
                status: "running",
                sourceReports: [])
        ]));

        var result = await handler.Handle(new ListDatasetPreparationsQuery(), CancellationToken.None);

        var item = Assert.Single(result.Items);
        Assert.Equal("running", item.Status);
        Assert.Equal(1, item.BoardSourcesCount);
        Assert.Equal(1, item.DigitSourcesCount);
    }

    private static DatasetPreparationMetadataDto CreateMetadata(
        string preparationName,
        DateTimeOffset createdAtUtc,
        IReadOnlyList<CreateDatasetPreparationSourceDto> sources,
        string status = "queued",
        IReadOnlyList<DatasetPreparationSourceReportDto>? sourceReports = null)
    {
        return new DatasetPreparationMetadataDto(
            PreparationName: preparationName,
            Status: status,
            CreatedAtUtc: createdAtUtc,
            Sources: sources,
            SourceReports: sourceReports ?? sources
                .Select(source => new DatasetPreparationSourceReportDto(source.Name, source.Type, 0, 0, 0))
                .ToArray(),
            Warnings: []);
    }

    private sealed class InMemoryDatasetPreparationsGateway : IDatasetPreparationsGateway
    {
        private readonly IReadOnlyList<DatasetPreparationMetadataDto> _items;

        public InMemoryDatasetPreparationsGateway(params DatasetPreparationMetadataDto[] items)
        {
            _items = items;
        }

        public Task<IReadOnlyList<DatasetPreparationMetadataDto>> ListAsync(CancellationToken cancellationToken = default)
        {
            return Task.FromResult(_items);
        }

        public Task<DatasetPreparationMetadataDto?> GetByNameAsync(
            string preparationName,
            CancellationToken cancellationToken = default)
        {
            throw new NotSupportedException();
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
