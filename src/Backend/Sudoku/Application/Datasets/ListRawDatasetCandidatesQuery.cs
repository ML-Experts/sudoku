using MediatR;

namespace Sudoku.Application.Datasets;

public sealed record ListRawDatasetCandidatesQuery()
    : IRequest<ListRawDatasetCandidatesQueryResultDto>;
