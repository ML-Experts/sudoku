using System.Threading.Channels;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Sudoku.Application.Abstractions;
using Sudoku.Application.SudokuSolve;

namespace Sudoku.Infrastructure.Background;

public sealed class SudokuSolveBackgroundWorker : BackgroundService
{
    private readonly ChannelReader<SolveSessionWorkItemDto> _channelReader;
    private readonly IServiceScopeFactory _serviceScopeFactory;
    private readonly IBackgroundOperationCancellationRegistry _backgroundOperationCancellationRegistry;

    public SudokuSolveBackgroundWorker(
        ChannelReader<SolveSessionWorkItemDto> channelReader,
        IServiceScopeFactory serviceScopeFactory,
        IBackgroundOperationCancellationRegistry backgroundOperationCancellationRegistry)
    {
        _channelReader = channelReader;
        _serviceScopeFactory = serviceScopeFactory;
        _backgroundOperationCancellationRegistry = backgroundOperationCancellationRegistry;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await foreach (var workItem in _channelReader.ReadAllAsync(stoppingToken))
        {
            try
            {
                if (!_backgroundOperationCancellationRegistry.TryGetCancellationToken(
                        workItem.SolveSessionId,
                        out var sessionCancellationToken))
                {
                    throw new InvalidOperationException(
                        $"Missing cancellation registration for sudoku solve session {workItem.SolveSessionId}.");
                }

                using var linkedCancellationTokenSource =
                    CancellationTokenSource.CreateLinkedTokenSource(stoppingToken, sessionCancellationToken);
                using var scope = _serviceScopeFactory.CreateScope();
                var runner = scope.ServiceProvider.GetRequiredService<ISudokuSolveSessionRunner>();
                await runner.RunAsync(workItem, linkedCancellationTokenSource.Token);
            }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
            {
                break;
            }
            catch (Exception exception)
            {
                _ = exception;
            }
            finally
            {
                _backgroundOperationCancellationRegistry.Complete(workItem.SolveSessionId);
            }
        }
    }
}
