namespace Sudoku.Application.Trainings;

public sealed class TrainingRunDetailsNotFoundException : Exception
{
    public TrainingRunDetailsNotFoundException(string runName)
        : base($"Nie znaleziono runu treningowego {runName}.")
    {
        RunName = runName;
    }

    public string RunName { get; }
}

public sealed class TrainingRunDetailsConflictException : Exception
{
    public TrainingRunDetailsConflictException(string message)
        : base(message)
    {
    }
}

public sealed class TrainingRunReportInvalidException : Exception
{
    public TrainingRunReportInvalidException(string message, Exception? innerException = null)
        : base(message, innerException)
    {
    }
}
