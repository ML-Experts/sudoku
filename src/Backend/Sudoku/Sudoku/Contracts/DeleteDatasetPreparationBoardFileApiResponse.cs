namespace Sudoku.Contracts;

public sealed record DeleteDatasetPreparationBoardFileApiResponse(
    string PreparationName,
    string SourceName,
    string BoardFolderName,
    bool Deleted,
    int RemainingItemsCount);
