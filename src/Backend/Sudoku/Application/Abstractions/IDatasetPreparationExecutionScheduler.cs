using Sudoku.Application.Datasets;

namespace Sudoku.Application.Abstractions;

public interface IDatasetPreparationExecutionScheduler
{
    Task ScheduleAsync(
        DatasetPreparationWorkItemDto workItem,
        CancellationToken cancellationToken = default);
}
