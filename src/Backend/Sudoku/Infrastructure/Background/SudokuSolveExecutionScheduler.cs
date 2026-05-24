using System.Threading.Channels;
using Sudoku.Application.Abstractions;
using Sudoku.Application.SudokuSolve;

namespace Sudoku.Infrastructure.Background;

public sealed class SudokuSolveExecutionScheduler : ISudokuSolveExecutionScheduler
{
    private readonly ChannelWriter<SolveSessionWorkItemDto> _channelWriter;
    private readonly IBackgroundOperationCancellationRegistry _backgroundOperationCancellationRegistry;

    public SudokuSolveExecutionScheduler(
        ChannelWriter<SolveSessionWorkItemDto> channelWriter,
        IBackgroundOperationCancellationRegistry backgroundOperationCancellationRegistry)
    {
        _channelWriter = channelWriter;
        _backgroundOperationCancellationRegistry = backgroundOperationCancellationRegistry;
    }

    public Task ScheduleAsync(
        SolveSessionWorkItemDto workItem,
        CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        _backgroundOperationCancellationRegistry.Register(workItem.SolveSessionId);

        try
        {
            if (!_channelWriter.TryWrite(workItem))
            {
                throw new InvalidOperationException("Nie udało się dodać sesji solve do kolejki wykonania.");
            }
        }
        catch
        {
            _backgroundOperationCancellationRegistry.Complete(workItem.SolveSessionId);
            throw;
        }

        return Task.CompletedTask;
    }
}
