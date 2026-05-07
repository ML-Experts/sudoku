using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Auth;
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
                options => options.StartTrainingPath.StartsWith("/", StringComparison.Ordinal),
                $"{MlServiceOptions.SectionName}:StartTrainingPath must start with '/'.")
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
        services.AddTransient<IProcessedDatasetsGateway, ProcessedDatasetsGateway>();
        services.AddTransient<IModelsRegistryGateway, ModelsRegistryGateway>();
        services.AddTransient<IActiveModelPointerGateway, ActiveModelPointerGateway>();
        services.AddTransient<ITrainingRunsGateway, TrainingRunsGateway>();
        services.AddTransient<ITrainingReportsGateway, TrainingReportsGateway>();
        services.AddTransient<ITrainingArtifactsCleanupGateway, TrainingArtifactsCleanupGateway>();
        services.AddTransient<ITrainingEventsPathProvider, MlTrainingEventsPathProvider>();

        services.AddHttpClient<IMlPingGateway, MlPingHttpClient>(ConfigureMlHttpClient);
        services.AddHttpClient<IMlImageProcessingGateway, MlImageProcessingHttpClient>(ConfigureMlHttpClient);
        services.AddHttpClient<IMlDatasetsPreparationGateway, MlDatasetsPreparationHttpClient>(ConfigureMlHttpClient);
        services.AddHttpClient<IMlTrainingsGateway, MlTrainingsHttpClient>(ConfigureMlHttpClient);

        return services;
    }

    private static void ConfigureMlHttpClient(IServiceProvider serviceProvider, HttpClient client)
    {
        var options = serviceProvider.GetRequiredService<IOptions<MlServiceOptions>>().Value;

        client.BaseAddress = new Uri(options.BaseUrl, UriKind.Absolute);
        client.Timeout = TimeSpan.FromSeconds(options.TimeoutSeconds);
    }
}
