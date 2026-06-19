using MediatR;
using Sudoku.Application.Abstractions;
using Sudoku.Models.Datasets;

namespace Sudoku.Application.Datasets;

public sealed class GetDatasetPreparationFoldersQueryHandler
    : IRequestHandler<GetDatasetPreparationFoldersQuery, GetDatasetPreparationFoldersQueryResultDto>
{
    private readonly IDatasetPreparationsGateway _datasetPreparationsGateway;
    private readonly IDatasetPreparationArtifactsGateway _datasetPreparationArtifactsGateway;

    public GetDatasetPreparationFoldersQueryHandler(
        IDatasetPreparationsGateway datasetPreparationsGateway,
        IDatasetPreparationArtifactsGateway datasetPreparationArtifactsGateway)
    {
        _datasetPreparationsGateway = datasetPreparationsGateway;
        _datasetPreparationArtifactsGateway = datasetPreparationArtifactsGateway;
    }

    public async Task<GetDatasetPreparationFoldersQueryResultDto> Handle(
        GetDatasetPreparationFoldersQuery request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.PreparationName) || string.IsNullOrWhiteSpace(request.Type))
        {
            throw new InvalidOperationException(
                "GetDatasetPreparationFoldersQuery must be validated before handler execution.");
        }

        var preparationName = request.PreparationName.Trim();
        var type = request.Type.Trim().ToLowerInvariant();

        var metadata = await _datasetPreparationsGateway.GetByNameAsync(preparationName, cancellationToken);
        if (metadata is null)
        {
            throw new DatasetPreparationNotFoundException(preparationName);
        }

        EnsurePreparationCompleted(metadata);

        var items = await _datasetPreparationArtifactsGateway.GetSourceFolderNamesAsync(
            preparationName,
            type,
            cancellationToken);

        return new GetDatasetPreparationFoldersQueryResultDto(
            PreparationName: metadata.PreparationName,
            Type: type,
            Items: items,
            TotalCount: items.Count);
    }

    private static void EnsurePreparationCompleted(DatasetPreparationMetadataDto metadata)
    {
        if (!string.Equals(metadata.Status, DatasetPreparationStatus.Completed, StringComparison.OrdinalIgnoreCase))
        {
            throw new DatasetPreparationArtifactsNotReadyException(metadata.PreparationName, metadata.Status);
        }
    }
}
