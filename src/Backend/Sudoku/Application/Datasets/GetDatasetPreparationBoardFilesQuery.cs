using MediatR;

namespace Sudoku.Application.Datasets;

public sealed record GetDatasetPreparationBoardFilesQuery(
    string? PreparationName,
    string? SourceName,
    int? Page,
    int? PageSize)
    : IRequest<GetDatasetPreparationBoardFilesQueryResultDto>;
