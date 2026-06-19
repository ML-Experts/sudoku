using MediatR;
using Sudoku.Application.Abstractions;

namespace Sudoku.Application.Datasets;

public sealed class ListDatasetPreparationsQueryHandler
    : IRequestHandler<ListDatasetPreparationsQuery, ListDatasetPreparationsQueryResultDto>
{
    private readonly IDatasetPreparationsGateway _datasetPreparationsGateway;

    public ListDatasetPreparationsQueryHandler(IDatasetPreparationsGateway datasetPreparationsGateway)
    {
        _datasetPreparationsGateway = datasetPreparationsGateway;
    }

    public async Task<ListDatasetPreparationsQueryResultDto> Handle(
        ListDatasetPreparationsQuery request,
        CancellationToken cancellationToken)
    {
        var items = await _datasetPreparationsGateway.ListAsync(cancellationToken);
        var mappedItems = items
            .OrderByDescending(item => item.CreatedAtUtc)
            .Select(MapToDatasetPreparationListItemDto)
            .ToArray();

        return new ListDatasetPreparationsQueryResultDto(
            Items: mappedItems,
            TotalCount: mappedItems.Length);
    }

    private static DatasetPreparationListItemDto MapToDatasetPreparationListItemDto(
        DatasetPreparationMetadataDto metadata)
    {
        return new DatasetPreparationListItemDto(
            PreparationName: metadata.PreparationName,
            CreatedAtUtc: metadata.CreatedAtUtc,
            Status: metadata.Status,
            BoardSourcesCount: CountSources(metadata.Sources, "board"),
            DigitSourcesCount: CountSources(metadata.Sources, "digit"));
    }

    private static int CountSources(
        IReadOnlyList<CreateDatasetPreparationSourceDto> sources,
        string type)
    {
        return sources.Count(source => string.Equals(source.Type, type, StringComparison.OrdinalIgnoreCase));
    }
}
