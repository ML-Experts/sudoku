namespace Sudoku.Application.Trainings;

public sealed class ProcessedDatasetCannotStartTrainingException : Exception
{
    public ProcessedDatasetCannotStartTrainingException(string datasetName)
        : base($"Przygotowany dataset {datasetName} nie zawiera próbek możliwych do treningu.")
    {
        DatasetName = datasetName;
    }

    public string DatasetName { get; }
}
