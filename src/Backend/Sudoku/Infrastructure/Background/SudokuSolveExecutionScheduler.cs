using System.Threading.Channels;
using Sudoku.Application.SudokuSolve;

namespace Sudoku.Infrastructure.Background;

public sealed class SudokuSolveExecutionScheduler : ISudokuSolveExecutionScheduler
{
    private readonly ChannelWriter<SolveSessionWorkItemDto> _channelWriter;

    public SudokuSolveExecutionScheduler(ChannelWriter<SolveSessionWorkItemDto> channelWriter)
    {
        _channelWriter = channelWriter;
    }

    public Task ScheduleAsync(
        SolveSessionWorkItemDto workItem,
        CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        if (!_channelWriter.TryWrite(workItem))
        {
            throw new InvalidOperationException("Nie udało się dodać sesji solve do kolejki wykonania.");
        }

        return Task.CompletedTask;
    }
}
