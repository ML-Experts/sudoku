namespace Sudoku.Application.Trainings;

public sealed class TrainingRunStartFailedException : Exception
{
    public TrainingRunStartFailedException(string message, Exception? innerException = null)
        : base(message, innerException)
    {
    }
}
