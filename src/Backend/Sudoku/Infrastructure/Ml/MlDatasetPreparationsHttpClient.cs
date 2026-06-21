using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Datasets;
using Sudoku.Application.Ml;
using Sudoku.Infrastructure.Configuration;

namespace Sudoku.Infrastructure.Ml;

public sealed class MlDatasetPreparationsHttpClient : IMlDatasetPreparationsGateway
{
    private readonly HttpClient _httpClient;
    private readonly MlServiceOptions _options;
    private readonly ILogger<MlDatasetPreparationsHttpClient> _logger;

    public MlDatasetPreparationsHttpClient(
        HttpClient httpClient,
        IOptions<MlServiceOptions> options,
        ILogger<MlDatasetPreparationsHttpClient> logger)
    {
        _httpClient = httpClient;
        _options = options.Value;
        _logger = logger;
    }

    public async Task<CreateDatasetPreparationMlResultDto> CreateAsync(
        CreateDatasetPreparationMlRequestDto request,
        CancellationToken cancellationToken = default)
    {
        var payload = new CreateDatasetPreparationApiEntryContract(
            PreparationName: request.PreparationName,
            Sources: request.Sources
                .Select(source => new CreateDatasetPreparationSourceApiEntryContract(
                    Name: source.Name,
                    Type: source.Type))
                .ToArray());

        try
        {
            using var response = await _httpClient.PostAsJsonAsync(
                _options.DatasetPreparationsPath,
                payload,
                cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                await ThrowMappedExceptionAsync(response, cancellationToken);
            }

            var responsePayload = await response.Content.ReadFromJsonAsync<CreateDatasetPreparationApiResponseContract>(
                cancellationToken: cancellationToken);

            if (responsePayload?.SourceReports is null)
            {
                throw new MlOperationFailedException(
                    CreateDatasetPreparationErrorTypes.PreparationInvariantViolation,
                    "Serwis ML zwrócił niepełny payload przygotowania datasetu.");
            }

            return new CreateDatasetPreparationMlResultDto(
                PreparationName: responsePayload.PreparationName ?? string.Empty,
                CreatedAtUtc: responsePayload.CreatedAtUtc,
                Status: responsePayload.Status,
                SourceReports: responsePayload.SourceReports
                    .Select(report => new DatasetPreparationMlSourceReportDto(
                        Name: report.Name ?? string.Empty,
                        Type: report.Type ?? string.Empty,
                        PreparedItemsCount: report.PreparedItemsCount,
                        RejectedItemsCount: report.RejectedItemsCount,
                        EmptyCellCount: report.EmptyCellCount))
                    .ToArray(),
                Warnings: responsePayload.Warnings ?? Array.Empty<string>());
        }
        catch (OperationCanceledException exception) when (!cancellationToken.IsCancellationRequested)
        {
            _logger.LogError(
                exception,
                "Przygotowanie datasetu po stronie ML przekroczylo timeout dla preparation {PreparationName}.",
                request.PreparationName);
            throw new MlServiceTimeoutException("Upłynął limit czasu odpowiedzi serwisu ML.");
        }
        catch (HttpRequestException exception)
        {
            _logger.LogError(
                exception,
                "Wywolanie przygotowania datasetu zakończylo się błędem sieci dla preparation {PreparationName}.",
                request.PreparationName);
            throw new MlServiceUnavailableException("Serwis ML jest niedostępny.");
        }
        catch (JsonException exception)
        {
            _logger.LogError(
                exception,
                "Serwis ML zwrócił niepoprawny JSON dla preparation {PreparationName}.",
                request.PreparationName);
            throw new MlOperationFailedException(
                CreateDatasetPreparationErrorTypes.PreparationInvariantViolation,
                "Serwis ML zwrócił nieprawidłowy payload JSON.");
        }
        catch (NotSupportedException exception)
        {
            _logger.LogError(
                exception,
                "Serwis ML zwrócił nieobsługiwany format JSON dla preparation {PreparationName}.",
                request.PreparationName);
            throw new MlOperationFailedException(
                CreateDatasetPreparationErrorTypes.PreparationInvariantViolation,
                "Serwis ML zwrócił odpowiedź w nieobsługiwanym formacie.");
        }
    }

    private async Task ThrowMappedExceptionAsync(HttpResponseMessage response, CancellationToken cancellationToken)
    {
        var errorPayload = await TryReadErrorPayloadAsync(response, cancellationToken);
        var message = string.IsNullOrWhiteSpace(errorPayload?.Message)
            ? $"Serwis ML zwrócił status HTTP {(int)response.StatusCode}."
            : errorPayload.Message;

        if (response.StatusCode == HttpStatusCode.ServiceUnavailable)
        {
            throw new MlServiceUnavailableException(message);
        }

        if (response.StatusCode is HttpStatusCode.RequestTimeout or HttpStatusCode.GatewayTimeout)
        {
            throw new MlServiceTimeoutException(message);
        }

        if ((int)response.StatusCode >= 500)
        {
            throw new MlServiceUnavailableException(message);
        }

        var errorType = string.IsNullOrWhiteSpace(errorPayload?.ErrorType)
            ? CreateDatasetPreparationErrorTypes.PreparationFailed
            : errorPayload.ErrorType;

        throw new MlOperationFailedException(errorType, message);
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

    private sealed record CreateDatasetPreparationApiEntryContract(
        string PreparationName,
        IReadOnlyList<CreateDatasetPreparationSourceApiEntryContract> Sources);

    private sealed record CreateDatasetPreparationSourceApiEntryContract(
        string Name,
        string Type);

    private sealed record CreateDatasetPreparationApiResponseContract(
        string? PreparationName,
        DateTimeOffset? CreatedAtUtc,
        string? Status,
        IReadOnlyList<DatasetPreparationSourceApiResponseContract>? SourceReports,
        IReadOnlyList<string>? Warnings);

    private sealed record DatasetPreparationSourceApiResponseContract(
        string? Name,
        string? Type,
        int PreparedItemsCount,
        int RejectedItemsCount,
        int EmptyCellCount);

    private sealed record ErrorApiResponseContract(
        string? ErrorType,
        string? Message);
}
