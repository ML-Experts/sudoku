using System.Threading.Channels;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Auth;
using Sudoku.Application.Datasets;
using Sudoku.Application.SudokuSolve;
using Sudoku.Infrastructure.Background;
using Sudoku.Infrastructure.Auth;
using Sudoku.Infrastructure.Configuration;
using Sudoku.Infrastructure.Ml;
using Sudoku.Infrastructure.Storage;

namespace Sudoku.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(this IServiceCollection services, IConfiguration configuration)
    {
        services.AddSingleton<TimeProvider>(TimeProvider.System);
        services.AddSingleton<IAdminAccessTokenFactory, JwtAdminAccessTokenFactory>();

        services
            .AddOptions<MlServiceOptions>()
            .Bind(configuration.GetSection(MlServiceOptions.SectionName))
            .ValidateDataAnnotations()
            .Validate(
                options => Uri.TryCreate(options.BaseUrl, UriKind.Absolute, out _),
                $"{MlServiceOptions.SectionName}:BaseUrl must be an absolute URL.")
            .Validate(
                options => options.PingPath.StartsWith("/", StringComparison.Ordinal),
                $"{MlServiceOptions.SectionName}:PingPath must start with '/'.")
            .Validate(
                options => options.PreprocessBoardPath.StartsWith("/", StringComparison.Ordinal),
                $"{MlServiceOptions.SectionName}:PreprocessBoardPath must start with '/'.")
            .Validate(
                options => options.PreprocessCellsPath.StartsWith("/", StringComparison.Ordinal),
                $"{MlServiceOptions.SectionName}:PreprocessCellsPath must start with '/'.")
            .Validate(
                options => options.CellInferencePath.StartsWith("/", StringComparison.Ordinal),
                $"{MlServiceOptions.SectionName}:CellInferencePath must start with '/'.")
            .Validate(
                options => options.SudokuOverlayCellsPath.StartsWith("/", StringComparison.Ordinal),
                $"{MlServiceOptions.SectionName}:SudokuOverlayCellsPath must start with '/'.")
            .Validate(
                options => options.PrepareDatasetPath.StartsWith("/", StringComparison.Ordinal),
                $"{MlServiceOptions.SectionName}:PrepareDatasetPath must start with '/'.")
            .Validate(
                options => options.DatasetPreparationsPath.StartsWith("/", StringComparison.Ordinal),
                $"{MlServiceOptions.SectionName}:DatasetPreparationsPath must start with '/'.")
            .Validate(
                options => options.StartTrainingPath.StartsWith("/", StringComparison.Ordinal),
                $"{MlServiceOptions.SectionName}:StartTrainingPath must start with '/'.")
            .Validate(
                options => options.TrainingEventsPathTemplate.StartsWith("/", StringComparison.Ordinal),
                $"{MlServiceOptions.SectionName}:TrainingEventsPathTemplate must start with '/'.")
            .Validate(
                options => options.CancelTrainingPathTemplate.StartsWith("/", StringComparison.Ordinal),
                $"{MlServiceOptions.SectionName}:CancelTrainingPathTemplate must start with '/'.")
            .Validate(
                options => options.CancelTrainingPathTemplate.Contains("{runName}", StringComparison.Ordinal),
                $"{MlServiceOptions.SectionName}:CancelTrainingPathTemplate must contain '{{runName}}'.")
            .Validate(
                options => options.TrainingEventsPathTemplate.Contains("{runName}", StringComparison.Ordinal),
                $"{MlServiceOptions.SectionName}:TrainingEventsPathTemplate must contain '{{runName}}'.")
            .ValidateOnStart();

        services.AddTransient<IFileStorageGateway, LocalFileStorageGateway>();
        services.AddTransient<IDatasetPreparationsGateway, DatasetPreparationsGateway>();
        services.AddTransient<IDatasetPreparationArtifactsGateway, DatasetPreparationArtifactsGateway>();
        services.AddTransient<IProcessedDatasetsGateway, ProcessedDatasetsGateway>();
        services.AddTransient<IModelsRegistryGateway, ModelsRegistryGateway>();
        services.AddTransient<IActiveModelPointerGateway, ActiveModelPointerGateway>();
        services.AddTransient<ITrainingRunsGateway, TrainingRunsGateway>();
        services.AddTransient<ITrainingReportsGateway, TrainingReportsGateway>();
        services.AddTransient<ITrainingArtifactsCleanupGateway, TrainingArtifactsCleanupGateway>();
        services.AddTransient<ITrainingEventsPathProvider, MlTrainingEventsPathProvider>();
        services.AddTransient<ISolveSessionsGateway, SolveSessionsGateway>();
        services.AddSingleton<IBackgroundOperationCancellationRegistry, InMemoryBackgroundOperationCancellationRegistry>();

        services.AddSingleton(_ => Channel.CreateUnbounded<DatasetPreparationWorkItemDto>(
            new UnboundedChannelOptions
            {
                SingleReader = true,
                SingleWriter = false,
                AllowSynchronousContinuations = false
            }));
        services.AddSingleton<ChannelReader<DatasetPreparationWorkItemDto>>(serviceProvider =>
            serviceProvider.GetRequiredService<Channel<DatasetPreparationWorkItemDto>>().Reader);
        services.AddSingleton<ChannelWriter<DatasetPreparationWorkItemDto>>(serviceProvider =>
            serviceProvider.GetRequiredService<Channel<DatasetPreparationWorkItemDto>>().Writer);
        services.AddSingleton<IDatasetPreparationExecutionScheduler, DatasetPreparationExecutionScheduler>();
        services.AddHostedService<DatasetPreparationBackgroundWorker>();
        services.AddHostedService<DatasetPreparationRecoveryHostedService>();

        services.AddSingleton(_ => Channel.CreateUnbounded<SolveSessionWorkItemDto>(
            new UnboundedChannelOptions
            {
                SingleReader = true,
                SingleWriter = false,
                AllowSynchronousContinuations = false
            }));
        services.AddSingleton<ChannelReader<SolveSessionWorkItemDto>>(serviceProvider =>
            serviceProvider.GetRequiredService<Channel<SolveSessionWorkItemDto>>().Reader);
        services.AddSingleton<ChannelWriter<SolveSessionWorkItemDto>>(serviceProvider =>
            serviceProvider.GetRequiredService<Channel<SolveSessionWorkItemDto>>().Writer);
        services.AddSingleton<ISudokuSolveExecutionScheduler, SudokuSolveExecutionScheduler>();
        services.AddHostedService<SudokuSolveBackgroundWorker>();

        services.AddHttpClient<IMlPingGateway, MlPingHttpClient>(ConfigureMlHttpClient);
        services.AddHttpClient<IMlImageProcessingGateway, MlImageProcessingHttpClient>(ConfigureMlHttpClient);
        services.AddHttpClient<IMlDatasetPreparationsGateway, MlDatasetPreparationsHttpClient>(ConfigureLongRunningMlHttpClient);
        services.AddHttpClient<IMlDatasetsPreparationGateway, MlDatasetsPreparationHttpClient>(ConfigureLongRunningMlHttpClient);
        services.AddHttpClient<IMlTrainingsGateway, MlTrainingsHttpClient>(ConfigureLongRunningMlHttpClient);

        return services;
    }

    private static void ConfigureMlHttpClient(IServiceProvider serviceProvider, HttpClient client)
    {
        var options = serviceProvider.GetRequiredService<IOptions<MlServiceOptions>>().Value;

        client.BaseAddress = new Uri(options.BaseUrl, UriKind.Absolute);
        client.Timeout = TimeSpan.FromSeconds(options.TimeoutSeconds);
    }

    private static void ConfigureLongRunningMlHttpClient(IServiceProvider serviceProvider, HttpClient client)
    {
        var options = serviceProvider.GetRequiredService<IOptions<MlServiceOptions>>().Value;

        client.BaseAddress = new Uri(options.BaseUrl, UriKind.Absolute);
        client.Timeout = options.LongRunningTimeoutSeconds <= 0
            ? Timeout.InfiniteTimeSpan
            : TimeSpan.FromSeconds(options.LongRunningTimeoutSeconds);
    }
}
