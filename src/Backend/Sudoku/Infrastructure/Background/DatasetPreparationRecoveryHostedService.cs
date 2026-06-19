using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Sudoku.Application.Datasets;

namespace Sudoku.Infrastructure.Background;

public sealed class DatasetPreparationRecoveryHostedService : IHostedService
{
    private readonly IServiceScopeFactory _serviceScopeFactory;
    private readonly ILogger<DatasetPreparationRecoveryHostedService> _logger;

    public DatasetPreparationRecoveryHostedService(
        IServiceScopeFactory serviceScopeFactory,
        ILogger<DatasetPreparationRecoveryHostedService> logger)
    {
        _serviceScopeFactory = serviceScopeFactory;
        _logger = logger;
    }

    public async Task StartAsync(CancellationToken cancellationToken)
    {
        try
        {
            using var scope = _serviceScopeFactory.CreateScope();
            var recovery = scope.ServiceProvider.GetRequiredService<IDatasetPreparationRecovery>();
            await recovery.RecoverAsync(cancellationToken);
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
        }
        catch (Exception exception)
        {
            _logger.LogError(exception, "Nie udalo sie wykonac recovery przygotowan datasetow po starcie backendu.");
        }
    }

    public Task StopAsync(CancellationToken cancellationToken)
    {
        return Task.CompletedTask;
    }
}
