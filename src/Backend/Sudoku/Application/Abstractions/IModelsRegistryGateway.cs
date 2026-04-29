using Sudoku.Application.ModelsRegistry;

namespace Sudoku.Application.Abstractions;

public interface IModelsRegistryGateway
{
    Task<IReadOnlyList<RegistryModelManifestDto>> ListAsync(
        CancellationToken cancellationToken = default);

    Task<RegistryModelManifestDto?> GetByNameAsync(
        string modelName,
        CancellationToken cancellationToken = default);

    Task FinalizeTrainedModelAsync(
        FinalizeTrainedModelManifestDto manifest,
        CancellationToken cancellationToken = default);
}
