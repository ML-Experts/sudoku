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

public sealed class MlDatasetsPreparationHttpClient : IMlDatasetsPreparationGateway
{
    private const string DefaultOperationErrorType = "dataset_source_invalid";

    private readonly HttpClient _httpClient;
    private readonly MlServiceOptions _options;
    private readonly ILogger<MlDatasetsPreparationHttpClient> _logger;

    public MlDatasetsPreparationHttpClient(
        HttpClient httpClient,
        IOptions<MlServiceOptions> options,
        ILogger<MlDatasetsPreparationHttpClient> logger)
    {
        _httpClient = httpClient;
        _options = options.Value;
        _logger = logger;
    }

    public async Task<PrepareDatasetArtifactResultDto> PrepareDatasetArtifactAsync(
        PrepareDatasetArtifactRequestDto request,
        CancellationToken cancellationToken = default)
    {
        var payload = new PrepareDatasetArtifactApiEntryContract(
            DatasetName: request.DatasetName,
            Sources: request.Sources
                .Select(source => new PrepareDatasetSourceApiEntryContract(
                    Name: source.Name,
                    Type: source.Type,
                    SplitPolicy: new DatasetSplitPolicyApiEntryContract(
                        Mode: source.SplitPolicy.Mode,
                        Ratios: new SplitRatiosApiEntryContract(
                            Train: source.SplitPolicy.Ratios.Train,
                            Val: source.SplitPolicy.Ratios.Val,
                            Test: source.SplitPolicy.Ratios.Test),
                        GroupBy: source.SplitPolicy.GroupBy)))
                .ToArray(),
            PreprocessingProfile: request.PreprocessingProfile);

        try
        {
            using var response = await _httpClient.PostAsJsonAsync(
                _options.PrepareDatasetPath,
                payload,
                cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                await ThrowMappedExceptionAsync(response, cancellationToken);
            }

            var responsePayload = await response.Content.ReadFromJsonAsync<PreparedDatasetArtifactApiResponseContract>(
                cancellationToken: cancellationToken);

            if (responsePayload?.SampleCounts is null || responsePayload.Sources is null)
            {
                throw new MlOperationFailedException(
                    DefaultOperationErrorType,
                    "Serwis ML zwrócił niepełny payload przygotowania datasetu.");
            }

            return new PrepareDatasetArtifactResultDto(
                SampleCounts: new SplitSampleCountsDto(
                    Train: responsePayload.SampleCounts.Train,
                    Val: responsePayload.SampleCounts.Val,
                    Test: responsePayload.SampleCounts.Test),
                Sources: responsePayload.Sources
                    .Select(source => new PreparedDatasetSourceReportDto(
                        Name: source.Name ?? string.Empty,
                        RequestedType: source.RequestedType ?? string.Empty,
                        DetectedType: source.DetectedType ?? string.Empty,
                        ProcessedSampleCount: source.ProcessedSampleCount,
                        IncludedSampleCount: source.IncludedSampleCount,
                        EmptyCellCount: source.EmptyCellCount,
                        RejectedSampleCount: source.RejectedSampleCount,
                        Warnings: source.Warnings ?? Array.Empty<string>()))
                    .ToArray(),
                Warnings: responsePayload.Warnings ?? Array.Empty<string>());
        }
        catch (OperationCanceledException exception) when (!cancellationToken.IsCancellationRequested)
        {
            _logger.LogError(
                exception,
                "Przygotowanie datasetu po stronie ML przekroczyło timeout dla datasetu {DatasetName}.",
                request.DatasetName);
            throw new MlServiceTimeoutException("Upłynął limit czasu odpowiedzi serwisu ML.");
        }
        catch (HttpRequestException exception)
        {
            _logger.LogError(
                exception,
                "Wywołanie przygotowania datasetu zakończyło się błędem sieci dla datasetu {DatasetName}.",
                request.DatasetName);
            throw new MlServiceUnavailableException("Serwis ML jest niedostępny.");
        }
        catch (JsonException exception)
        {
            _logger.LogError(
                exception,
                "Serwis ML zwrócił niepoprawny JSON dla datasetu {DatasetName}.",
                request.DatasetName);
            throw new MlOperationFailedException(
                DefaultOperationErrorType,
                "Serwis ML zwrócił nieprawidłowy payload JSON.");
        }
        catch (NotSupportedException exception)
        {
            _logger.LogError(
                exception,
                "Serwis ML zwrócił nieobsługiwany format JSON dla datasetu {DatasetName}.",
                request.DatasetName);
            throw new MlOperationFailedException(
                DefaultOperationErrorType,
                "Serwis ML zwrócił odpowiedź w nieobsługiwanym formacie.");
        }
    }

    private async Task ThrowMappedExceptionAsync(HttpResponseMessage response, CancellationToken cancellationToken)
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

        var errorType = string.IsNullOrWhiteSpace(errorPayload?.ErrorType)
            ? DefaultOperationErrorType
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

    private sealed record PrepareDatasetArtifactApiEntryContract(
        string DatasetName,
        IReadOnlyList<PrepareDatasetSourceApiEntryContract> Sources,
        string PreprocessingProfile);

    private sealed record PrepareDatasetSourceApiEntryContract(
        string Name,
        string Type,
        DatasetSplitPolicyApiEntryContract SplitPolicy);

    private sealed record DatasetSplitPolicyApiEntryContract(
        string Mode,
        SplitRatiosApiEntryContract Ratios,
        string GroupBy);

    private sealed record SplitRatiosApiEntryContract(
        double Train,
        double Val,
        double Test);

    private sealed record PreparedDatasetArtifactApiResponseContract(
        SplitSampleCountsApiResponseContract? SampleCounts,
        IReadOnlyList<PreparedDatasetSourceReportApiResponseContract>? Sources,
        IReadOnlyList<string>? Warnings);

    private sealed record SplitSampleCountsApiResponseContract(
        int Train,
        int Val,
        int Test);

    private sealed record PreparedDatasetSourceReportApiResponseContract(
        string? Name,
        string? RequestedType,
        string? DetectedType,
        int ProcessedSampleCount,
        int IncludedSampleCount,
        int EmptyCellCount,
        int RejectedSampleCount,
        IReadOnlyList<string>? Warnings);

    private sealed record ErrorApiResponseContract(
        string? ErrorType,
        string? Message);
}
