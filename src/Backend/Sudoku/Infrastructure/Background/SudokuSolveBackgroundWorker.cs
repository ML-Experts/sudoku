using System.Threading.Channels;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Sudoku.Application.SudokuSolve;

namespace Sudoku.Infrastructure.Background;

public sealed class SudokuSolveBackgroundWorker : BackgroundService
{
    private readonly ChannelReader<SolveSessionWorkItemDto> _channelReader;
    private readonly IServiceScopeFactory _serviceScopeFactory;

    public SudokuSolveBackgroundWorker(
        ChannelReader<SolveSessionWorkItemDto> channelReader,
        IServiceScopeFactory serviceScopeFactory)
    {
        _channelReader = channelReader;
        _serviceScopeFactory = serviceScopeFactory;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await foreach (var workItem in _channelReader.ReadAllAsync(stoppingToken))
        {
            try
            {
                using var scope = _serviceScopeFactory.CreateScope();
                var runner = scope.ServiceProvider.GetRequiredService<ISudokuSolveSessionRunner>();
                await runner.RunAsync(workItem, stoppingToken);
            }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
            {
                break;
            }
            catch (Exception exception)
            {
                _ = exception;
            }
        }
    }
}
