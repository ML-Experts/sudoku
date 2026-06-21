using Sudoku.Application.Datasets;

namespace Sudoku.Application.Abstractions;

public interface IDatasetPreparationsGateway
{
    Task<IReadOnlyList<DatasetPreparationMetadataDto>> ListAsync(
        CancellationToken cancellationToken = default);

    Task<DatasetPreparationMetadataDto?> GetByNameAsync(
        string preparationName,
        CancellationToken cancellationToken = default);

    Task<bool> TryCreateAsync(
        DatasetPreparationMetadataDto metadata,
        CancellationToken cancellationToken = default);

    Task UpdateAsync(
        DatasetPreparationMetadataDto metadata,
        CancellationToken cancellationToken = default);

    Task CleanupGeneratedContentAsync(
        string preparationName,
        CancellationToken cancellationToken = default);
}
