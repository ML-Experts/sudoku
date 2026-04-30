namespace Sudoku.Application.Trainings;

public interface ITrainingRunEventLockProvider
{
    ValueTask<IAsyncDisposable> AcquireAsync(
        string runName,
        CancellationToken cancellationToken = default);
}
