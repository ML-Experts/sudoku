using MediatR;
using Sudoku.Application.Abstractions;

namespace Sudoku.Application.Datasets;

public sealed class ListProcessedDatasetsQueryHandler
    : IRequestHandler<ListProcessedDatasetsQuery, ListProcessedDatasetsQueryResultDto>
{
    private readonly IProcessedDatasetsGateway _processedDatasetsGateway;

    public ListProcessedDatasetsQueryHandler(IProcessedDatasetsGateway processedDatasetsGateway)
    {
        _processedDatasetsGateway = processedDatasetsGateway;
    }

    public async Task<ListProcessedDatasetsQueryResultDto> Handle(
        ListProcessedDatasetsQuery request,
        CancellationToken cancellationToken)
    {
        var items = await _processedDatasetsGateway.ListAsync(cancellationToken);
        var mappedItems = items
            .OrderByDescending(item => item.CreatedAtUtc)
            .Select(item => new ProcessedDatasetListItemDto(
                Name: item.Name,
                FileName: item.FileName,
                PreprocessingProfile: item.PreprocessingProfile,
                CreatedAtUtc: item.CreatedAtUtc,
                SampleCounts: item.SampleCounts))
            .ToArray();

        return new ListProcessedDatasetsQueryResultDto(
            Items: mappedItems,
            TotalCount: mappedItems.Length);
    }
}
