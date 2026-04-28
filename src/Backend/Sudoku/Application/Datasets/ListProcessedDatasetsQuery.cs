using MediatR;

namespace Sudoku.Application.Datasets;

public sealed record ListProcessedDatasetsQuery()
    : IRequest<ListProcessedDatasetsQueryResultDto>;
