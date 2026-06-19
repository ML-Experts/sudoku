using MediatR;

namespace Sudoku.Application.Datasets;

public sealed record GetDatasetPreparationFoldersQuery(string? PreparationName, string? Type)
    : IRequest<GetDatasetPreparationFoldersQueryResultDto>;
