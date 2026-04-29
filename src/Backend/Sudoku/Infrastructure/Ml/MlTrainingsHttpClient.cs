using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Ml;
using Sudoku.Application.Trainings;
using Sudoku.Infrastructure.Configuration;

namespace Sudoku.Infrastructure.Ml;

public sealed class MlTrainingsHttpClient : IMlTrainingsGateway
{
    private readonly HttpClient _httpClient;
    private readonly MlServiceOptions _options;
    private readonly ILogger<MlTrainingsHttpClient> _logger;

    public MlTrainingsHttpClient(
        HttpClient httpClient,
        IOptions<MlServiceOptions> options,
        ILogger<MlTrainingsHttpClient> logger)
    {
        _httpClient = httpClient;
        _options = options.Value;
        _logger = logger;
    }

    public async Task<StartMlTrainingResultDto> StartTrainingAsync(
        StartMlTrainingRequestDto request,
        CancellationToken cancellationToken = default)
    {
        try
        {
            using var response = await _httpClient.PostAsJsonAsync(
                _options.StartTrainingPath,
                request,
                cancellationToken);

            if (response.StatusCode is not HttpStatusCode.Accepted and not HttpStatusCode.OK)
            {
                await ThrowMappedExceptionAsync(response, request.RunName, cancellationToken);
            }

            var responsePayload = await TryReadAcceptedPayloadAsync(response, request.RunName, cancellationToken);
            return new StartMlTrainingResultDto(
                AcceptedAtUtc: responsePayload?.AcceptedAtUtc,
                MlJobId: responsePayload?.MlJobId);
        }
        catch (OperationCanceledException exception) when (!cancellationToken.IsCancellationRequested)
        {
            _logger.LogError(
                exception,
                "Start treningu po stronie ML przekroczył timeout dla runu {RunName}.",
                request.RunName);
            throw new MlServiceTimeoutException("Upłynął limit czasu potwierdzenia startu treningu przez serwis ML.");
        }
        catch (HttpRequestException exception)
        {
            _logger.LogError(
                exception,
                "Wywołanie startu treningu zakończyło się błędem sieci dla runu {RunName}.",
                request.RunName);
            throw new MlServiceUnavailableException("Serwis ML jest niedostępny.");
        }
        catch (JsonException exception)
        {
            _logger.LogError(
                exception,
                "Serwis ML zwrócił niepoprawny JSON przy starcie runu {RunName}.",
                request.RunName);
            throw new MlOperationFailedException(
                CreateTrainingRunErrorTypes.MlTrainingStartRejected,
                "Serwis ML zwrócił nieprawidłowy payload JSON.");
        }
        catch (NotSupportedException exception)
        {
            _logger.LogError(
                exception,
                "Serwis ML zwrócił nieobsługiwany format odpowiedzi przy starcie runu {RunName}.",
                request.RunName);
            throw new MlOperationFailedException(
                CreateTrainingRunErrorTypes.MlTrainingStartRejected,
                "Serwis ML zwrócił odpowiedź w nieobsługiwanym formacie.");
        }
    }

    private async Task ThrowMappedExceptionAsync(
        HttpResponseMessage response,
        string runName,
        CancellationToken cancellationToken)
    {
        var statusCode = response.StatusCode;
        var errorPayload = await TryReadErrorPayloadAsync(response, cancellationToken);
        var message = string.IsNullOrWhiteSpace(errorPayload?.Message)
            ? $"Serwis ML zwrócił status HTTP {(int)statusCode}."
            : errorPayload.Message;

        if (statusCode == HttpStatusCode.ServiceUnavailable)
        {
            throw new MlServiceUnavailableException(message);
        }

        if (statusCode is HttpStatusCode.RequestTimeout or HttpStatusCode.GatewayTimeout)
        {
            throw new MlServiceTimeoutException(message);
        }

        if ((int)statusCode >= 500)
        {
            throw new MlServiceUnavailableException(message);
        }

        _logger.LogWarning(
            "Serwis ML odrzucił start runu {RunName} statusem HTTP {StatusCode}.",
            runName,
            (int)statusCode);

        var errorType = string.IsNullOrWhiteSpace(errorPayload?.ErrorType)
            ? CreateTrainingRunErrorTypes.MlTrainingStartRejected
            : errorPayload.ErrorType;

        throw new MlOperationFailedException(errorType, message);
    }

    private static async Task<AcceptedTrainingApiResponseContract?> TryReadAcceptedPayloadAsync(
        HttpResponseMessage response,
        string runName,
        CancellationToken cancellationToken)
    {
        if (response.Content.Headers.ContentLength == 0)
        {
            return null;
        }

        var payload = await response.Content.ReadFromJsonAsync<AcceptedTrainingApiResponseContract>(
            cancellationToken: cancellationToken);

        if (payload is null)
        {
            return null;
        }

        if (payload.Accepted.HasValue && !payload.Accepted.Value)
        {
            throw new MlOperationFailedException(
                CreateTrainingRunErrorTypes.MlTrainingStartRejected,
                $"Serwis ML nie potwierdził przyjęcia runu {runName}.");
        }

        return payload;
    }

    private static async Task<ErrorApiResponseContract?> TryReadErrorPayloadAsync(
        HttpResponseMessage response,
        CancellationToken cancellationToken)
    {
        try
        {
            return await response.Content.ReadFromJsonAsync<ErrorApiResponseContract>(cancellationToken: cancellationToken);
        }
        catch (JsonException)
        {
            return null;
        }
        catch (NotSupportedException)
        {
            return null;
        }
    }

    private sealed record AcceptedTrainingApiResponseContract(
        bool? Accepted,
        DateTimeOffset? AcceptedAtUtc,
        string? MlJobId);

    private sealed record ErrorApiResponseContract(
        string? ErrorType,
        string? Message);
}
