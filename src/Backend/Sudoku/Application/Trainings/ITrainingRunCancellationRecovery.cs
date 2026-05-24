namespace Sudoku.Application.Trainings;

public interface ITrainingRunCancellationRecovery
{
    Task RecoverAsync(CancellationToken cancellationToken = default);
}
