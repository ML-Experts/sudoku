using System.Threading.Channels;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Sudoku.Application.Datasets;

namespace Sudoku.Infrastructure.Background;

public sealed class DatasetPreparationBackgroundWorker : BackgroundService
{
    private readonly ChannelReader<DatasetPreparationWorkItemDto> _channelReader;
    private readonly IServiceScopeFactory _serviceScopeFactory;
    private readonly ILogger<DatasetPreparationBackgroundWorker> _logger;

    public DatasetPreparationBackgroundWorker(
        ChannelReader<DatasetPreparationWorkItemDto> channelReader,
        IServiceScopeFactory serviceScopeFactory,
        ILogger<DatasetPreparationBackgroundWorker> logger)
    {
        _channelReader = channelReader;
        _serviceScopeFactory = serviceScopeFactory;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await foreach (var workItem in _channelReader.ReadAllAsync(stoppingToken))
        {
            try
            {
                using var scope = _serviceScopeFactory.CreateScope();
                var runner = scope.ServiceProvider.GetRequiredService<DatasetPreparationJobRunner>();
                await runner.RunAsync(workItem.PreparationName, stoppingToken);
            }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
            {
                break;
            }
            catch (Exception exception)
            {
                _logger.LogError(
                    exception,
                    "Nieobsluzony wyjatek workera przygotowan datasetow dla preparation {PreparationName}.",
                    workItem.PreparationName);
            }
        }
    }
}
