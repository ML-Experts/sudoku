using Microsoft.Extensions.Options;
using Sudoku.Configuration;

namespace Sudoku.Infrastructure.Ml;

public sealed class MlPingClient : IMlPingClient
{
    private readonly HttpClient _httpClient;
    private readonly MlServiceOptions _options;
    private readonly ILogger<MlPingClient> _logger;

    public MlPingClient(
        HttpClient httpClient,
        IOptions<MlServiceOptions> options,
        ILogger<MlPingClient> logger)
    {
        _httpClient = httpClient;
        _options = options.Value;
        _logger = logger;
    }

    public async Task<MlPingResult> PingAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            using var response = await _httpClient.GetAsync(_options.PingPath, cancellationToken);

            if (response.IsSuccessStatusCode)
            {
                return new MlPingResult(
                    IsAvailable: true,
                    StatusCode: response.StatusCode,
                    Message: "Received pong from ML.");
            }

            _logger.LogWarning("ML ping returned status code {StatusCode}.", (int)response.StatusCode);

            return new MlPingResult(
                IsAvailable: false,
                StatusCode: response.StatusCode,
                Message: $"No pong from ML. ML service returned status code {(int)response.StatusCode}.");
        }
        catch (OperationCanceledException exception) when (!cancellationToken.IsCancellationRequested)
        {
            _logger.LogError(exception, "ML ping timed out.");

            return new MlPingResult(
                IsAvailable: false,
                StatusCode: null,
                Message: "No pong from ML. ML service request timed out.");
        }
        catch (HttpRequestException exception)
        {
            _logger.LogError(exception, "ML ping request failed.");

            return new MlPingResult(
                IsAvailable: false,
                StatusCode: null,
                Message: "No pong from ML. ML service is unreachable.");
        }
    }
}
