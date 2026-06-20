using MediatR;

namespace Sudoku.Application.Datasets;

public sealed record CreateProcessedDatasetCommand(
    string? PreparationName,
    string? Name,
    IReadOnlyList<SelectedRawDatasetSourceDto>? Sources)
    : IRequest<CreateProcessedDatasetCommandResultDto>;
