using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Infrastructure.Configuration;
using Sudoku.Infrastructure.Ml;
using Sudoku.Infrastructure.Storage;

namespace Sudoku.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(this IServiceCollection services, IConfiguration configuration)
    {
        services.AddSingleton<TimeProvider>(TimeProvider.System);

        services
            .AddOptions<MlServiceOptions>()
            .Bind(configuration.GetSection(MlServiceOptions.SectionName))
            .ValidateDataAnnotations()
            .Validate(
                options => Uri.TryCreate(options.BaseUrl, UriKind.Absolute, out _),
                $"{MlServiceOptions.SectionName}:BaseUrl must be an absolute URL.")
            .ValidateOnStart();

        services.AddTransient<IFileStorageGateway, LocalFileStorageGateway>();

        services.AddHttpClient<IMlPingGateway, MlPingHttpClient>(ConfigureMlHttpClient);
        services.AddHttpClient<IMlImageProcessingGateway, MlImageProcessingHttpClient>(ConfigureMlHttpClient);

        return services;
    }

    private static void ConfigureMlHttpClient(IServiceProvider serviceProvider, HttpClient client)
    {
        var options = serviceProvider.GetRequiredService<IOptions<MlServiceOptions>>().Value;

        client.BaseAddress = new Uri(options.BaseUrl, UriKind.Absolute);
        client.Timeout = TimeSpan.FromSeconds(options.TimeoutSeconds);
    }
}
