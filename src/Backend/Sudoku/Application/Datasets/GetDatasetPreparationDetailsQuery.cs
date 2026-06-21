using MediatR;

namespace Sudoku.Application.Datasets;

public sealed record GetDatasetPreparationDetailsQuery(string? PreparationName)
    : IRequest<GetDatasetPreparationDetailsQueryResultDto>;
