using Microsoft.Extensions.Configuration;

namespace Sudoku.Configuration;

public static class BackendConfigurationExtensions
{
    private const string DefaultRuntimeEnvironment = "local";
    private const string RuntimeEnvironmentOverrideKey = "SUDOKU_ENVIRONMENT";

    public static WebApplicationBuilder AddBackendConfiguration(this WebApplicationBuilder builder, string[] args)
    {
        var configurationRootPath = builder.Environment.ContentRootPath;

        var bootstrapConfiguration = new ConfigurationBuilder()
            .SetBasePath(configurationRootPath)
            .AddJsonFile("appsettings.json", optional: false, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddCommandLine(args)
            .Build();

        var runtimeEnvironment = ResolveRuntimeEnvironment(bootstrapConfiguration);

        builder.Configuration.Sources.Clear();
        builder.Configuration
            .SetBasePath(configurationRootPath)
            .AddJsonFile("appsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile($"appsettings.{runtimeEnvironment}.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddCommandLine(args);

        return builder;
    }

    private static string ResolveRuntimeEnvironment(IConfiguration configuration)
    {
        var runtimeEnvironment =
            configuration[RuntimeEnvironmentOverrideKey]
            ?? configuration[$"{BackendRuntimeOptions.SectionName}:{nameof(BackendRuntimeOptions.Environment)}"];

        return string.IsNullOrWhiteSpace(runtimeEnvironment)
            ? DefaultRuntimeEnvironment
            : runtimeEnvironment.Trim().ToLowerInvariant();
    }
}
