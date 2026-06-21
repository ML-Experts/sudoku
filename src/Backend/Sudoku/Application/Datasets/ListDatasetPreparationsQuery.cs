using MediatR;

namespace Sudoku.Application.Datasets;

public sealed record ListDatasetPreparationsQuery()
    : IRequest<ListDatasetPreparationsQueryResultDto>;
