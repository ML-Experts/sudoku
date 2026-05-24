namespace Sudoku.Application.Trainings;

public interface ITrainingRunNameGenerator
{
    string Generate(
        DateTimeOffset createdAtUtc,
        string runNamePrefix,
        string baseModelName,
        string processedDatasetName,
        int attempt);
}
