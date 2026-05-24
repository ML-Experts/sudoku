namespace Sudoku.Application.Trainings;

public sealed class ProcessedDatasetNotFoundException : Exception
{
    public ProcessedDatasetNotFoundException(string datasetName)
        : base($"Przygotowany dataset {datasetName} nie został odnaleziony.")
    {
        DatasetName = datasetName;
    }

    public string DatasetName { get; }
}
