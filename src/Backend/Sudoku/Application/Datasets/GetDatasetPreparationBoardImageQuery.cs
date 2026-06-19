using MediatR;

namespace Sudoku.Application.Datasets;

public sealed record GetDatasetPreparationBoardImageQuery(
    string? PreparationName,
    string? SourceName,
    string? BoardFolderName)
    : IRequest<GetDatasetPreparationBoardImageQueryResultDto>;
