using Sudoku.Application.Datasets;

namespace Sudoku.Application.Abstractions;

public interface IMlDatasetsPreparationGateway
{
    Task<PrepareDatasetArtifactResultDto> PrepareDatasetArtifactAsync(
        PrepareDatasetArtifactRequestDto request,
        CancellationToken cancellationToken = default);
}
