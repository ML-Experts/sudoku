namespace Sudoku.Application.Datasets;

public sealed record DeleteDatasetPreparationBoardFileCommandResultDto(
    string PreparationName,
    string SourceName,
    string BoardFolderName,
    bool Deleted,
    int RemainingItemsCount);
