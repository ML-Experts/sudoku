using MediatR;

namespace Sudoku.Application.Datasets;

public sealed record DeleteDatasetPreparationBoardFileCommand(
    string? PreparationName,
    string? SourceName,
    string? BoardFolderName)
    : IRequest<DeleteDatasetPreparationBoardFileCommandResultDto>;
