namespace Sudoku.Application.Datasets;

public sealed class DatasetPreparationSourceNotFoundException : Exception
{
    public DatasetPreparationSourceNotFoundException(string preparationName, string sourceName)
        : base($"Nie znaleziono źródła '{sourceName}' w przygotowaniu datasetu '{preparationName}'.")
    {
        PreparationName = preparationName;
        SourceName = sourceName;
    }

    public string PreparationName { get; }

    public string SourceName { get; }
}
