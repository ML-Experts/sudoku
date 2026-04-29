namespace Sudoku.Application.Trainings;

public sealed class TrainingRunNotFoundForRealtimeException : Exception
{
    public TrainingRunNotFoundForRealtimeException(string runName)
        : base($"Nie znaleziono runu treningowego {runName} do monitorowania realtime.")
    {
        RunName = runName;
    }

    public string RunName { get; }
}
