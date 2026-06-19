using System.Threading.Channels;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Datasets;

namespace Sudoku.Infrastructure.Background;

public sealed class DatasetPreparationExecutionScheduler : IDatasetPreparationExecutionScheduler
{
    private readonly ChannelWriter<DatasetPreparationWorkItemDto> _channelWriter;

    public DatasetPreparationExecutionScheduler(ChannelWriter<DatasetPreparationWorkItemDto> channelWriter)
    {
        _channelWriter = channelWriter;
    }

    public Task ScheduleAsync(
        DatasetPreparationWorkItemDto workItem,
        CancellationToken cancellationToken = default)
    {
        return _channelWriter.WriteAsync(workItem, cancellationToken).AsTask();
    }
}
