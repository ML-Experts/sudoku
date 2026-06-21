namespace Sudoku.Application.Datasets;

public sealed class DatasetPreparationArtifactsNotReadyException : Exception
{
    public DatasetPreparationArtifactsNotReadyException(string preparationName, string status)
        : base(
            $"Przygotowanie datasetu '{preparationName}' ma status '{status}' i nie jest gotowe do odczytu artefaktów.")
    {
        PreparationName = preparationName;
        Status = status;
    }

    public string PreparationName { get; }

    public string Status { get; }
}
