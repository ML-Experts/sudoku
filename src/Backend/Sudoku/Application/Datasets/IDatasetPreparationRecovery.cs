namespace Sudoku.Application.Datasets;

public interface IDatasetPreparationRecovery
{
    Task RecoverAsync(CancellationToken cancellationToken = default);
}
