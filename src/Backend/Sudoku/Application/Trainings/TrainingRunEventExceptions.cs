namespace Sudoku.Application.Trainings;

public sealed class TrainingRunNotFoundException : Exception
{
    public TrainingRunNotFoundException(string runName)
        : base($"Nie znaleziono runu treningowego {runName}.")
    {
        RunName = runName;
    }

    public string RunName { get; }
}

public sealed class TrainingRunEventConflictException : Exception
{
    public TrainingRunEventConflictException(string message)
        : base(message)
    {
    }
}

public sealed class TrainingRunEventArtifactNotReadyException : Exception
{
    public TrainingRunEventArtifactNotReadyException(string message)
        : base(message)
    {
    }
}

public sealed class TrainingRunEventInvalidTransitionException : Exception
{
    public TrainingRunEventInvalidTransitionException(string message)
        : base(message)
    {
    }
}

public sealed class TrainingRunEventPersistenceException : Exception
{
    public TrainingRunEventPersistenceException(string message, Exception innerException)
        : base(message, innerException)
    {
    }
}
