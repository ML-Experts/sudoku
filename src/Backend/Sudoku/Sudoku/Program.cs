using Microsoft.Extensions.Options;
using Sudoku.Configuration;
using Sudoku.Contracts;
using Sudoku.Infrastructure.Ml;

var builder = WebApplication.CreateBuilder(args);

builder.Services
    .AddOptions<MlServiceOptions>()
    .BindConfiguration(MlServiceOptions.SectionName)
    .ValidateDataAnnotations()
    .Validate(
        options => Uri.TryCreate(options.BaseUrl, UriKind.Absolute, out _),
        $"{MlServiceOptions.SectionName}:BaseUrl must be an absolute URL.")
    .ValidateOnStart(); 

builder.Services.AddHttpClient<IMlPingClient, MlPingClient>((serviceProvider, client) =>
{
    var options = serviceProvider.GetRequiredService<IOptions<MlServiceOptions>>().Value;

    client.BaseAddress = new Uri(options.BaseUrl, UriKind.Absolute);
    client.Timeout = TimeSpan.FromSeconds(options.TimeoutSeconds);
});

var app = builder.Build();

app.MapGet("/api/ping", async (IMlPingClient mlPingClient, CancellationToken cancellationToken) =>
{
    var mlPingResult = await mlPingClient.PingAsync(cancellationToken);

    var response = new PingResponse(
        BackendStatus: "ok",
        MlStatus: mlPingResult.IsAvailable ? "ok" : "unavailable",
        TimestampUtc: DateTimeOffset.UtcNow,
        Message: mlPingResult.IsAvailable ? "pong" : mlPingResult.Message);

    return mlPingResult.IsAvailable
        ? Results.Ok(response)
        : Results.Json(response, statusCode: StatusCodes.Status503ServiceUnavailable);
})
.WithName("Ping");

app.Run();
