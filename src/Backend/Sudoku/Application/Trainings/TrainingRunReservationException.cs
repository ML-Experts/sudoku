namespace Sudoku.Application.Trainings;

public sealed class TrainingRunReservationException : Exception
{
    public TrainingRunReservationException(string message)
        : base(message)
    {
    }
}
