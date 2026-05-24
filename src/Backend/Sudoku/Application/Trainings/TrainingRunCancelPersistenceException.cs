namespace Sudoku.Application.Trainings;

public sealed class TrainingRunCancelPersistenceException : Exception
{
    public TrainingRunCancelPersistenceException(string message, Exception innerException)
        : base(message, innerException)
    {
    }
}
