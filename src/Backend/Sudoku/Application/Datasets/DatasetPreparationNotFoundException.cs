namespace Sudoku.Application.Datasets;

public sealed class DatasetPreparationNotFoundException : Exception
{
    public DatasetPreparationNotFoundException(string preparationName)
        : base($"Nie znaleziono przygotowania datasetu {preparationName}.")
    {
        PreparationName = preparationName;
    }

    public string PreparationName { get; }
}
