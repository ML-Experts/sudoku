namespace Sudoku.Application.Datasets;

public sealed class DatasetPreparationBoardFileNotFoundException : Exception
{
    public DatasetPreparationBoardFileNotFoundException(
        string preparationName,
        string sourceName,
        string boardFolderName)
        : base(
            $"Nie znaleziono planszy '{boardFolderName}' w źródle '{sourceName}' przygotowania datasetu '{preparationName}'.")
    {
        PreparationName = preparationName;
        SourceName = sourceName;
        BoardFolderName = boardFolderName;
    }

    public string PreparationName { get; }

    public string SourceName { get; }

    public string BoardFolderName { get; }
}
