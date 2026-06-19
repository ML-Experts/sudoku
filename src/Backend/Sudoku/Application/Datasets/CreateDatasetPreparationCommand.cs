using MediatR;

namespace Sudoku.Application.Datasets;

public sealed record CreateDatasetPreparationCommand(
    string? PreparationName,
    IReadOnlyList<CreateDatasetPreparationSourceDto>? Sources)
    : IRequest<CreateDatasetPreparationCommandResultDto>;
