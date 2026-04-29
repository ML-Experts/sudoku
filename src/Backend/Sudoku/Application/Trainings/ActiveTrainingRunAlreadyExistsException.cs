namespace Sudoku.Application.Trainings;

public sealed class ActiveTrainingRunAlreadyExistsException : Exception
{
    public ActiveTrainingRunAlreadyExistsException(string activeRunName)
        : base($"Istnieje już aktywny run treningowy {activeRunName}.")
    {
        ActiveRunName = activeRunName;
    }

    public string ActiveRunName { get; }
}
