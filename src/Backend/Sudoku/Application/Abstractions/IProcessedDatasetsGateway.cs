using Sudoku.Application.Datasets;

namespace Sudoku.Application.Abstractions;

public interface IProcessedDatasetsGateway
{
    Task<bool> IsProcessedDatasetNameAvailableAsync(
        string datasetName,
        CancellationToken cancellationToken = default);

    Task PromotePreparedArtifactAsync(
        string datasetName,
        string targetFileName,
        CancellationToken cancellationToken = default);

    Task SaveMetadataAsync(
        ProcessedDatasetMetadataDto metadata,
        CancellationToken cancellationToken = default);

    Task<IReadOnlyList<ProcessedDatasetMetadataDto>> ListAsync(
        CancellationToken cancellationToken = default);

    Task<ProcessedDatasetMetadataDto?> GetByNameAsync(
        string datasetName,
        CancellationToken cancellationToken = default);
}
