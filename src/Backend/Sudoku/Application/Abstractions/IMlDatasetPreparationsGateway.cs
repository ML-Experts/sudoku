using Sudoku.Application.Datasets;

namespace Sudoku.Application.Abstractions;

public interface IMlDatasetPreparationsGateway
{
    Task<CreateDatasetPreparationMlResultDto> CreateAsync(
        CreateDatasetPreparationMlRequestDto request,
        CancellationToken cancellationToken = default);
}
