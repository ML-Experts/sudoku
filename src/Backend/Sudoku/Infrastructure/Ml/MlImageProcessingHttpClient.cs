using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Ml;
using Sudoku.Application.Sudoku;
using Sudoku.Infrastructure.Configuration;
using Sudoku.Models.Images;

namespace Sudoku.Infrastructure.Ml;

public sealed class MlImageProcessingHttpClient : IMlImageProcessingGateway
{
    private const string DefaultOperationErrorType = "ml_operation_failed";

    private readonly HttpClient _httpClient;
    private readonly MlServiceOptions _options;
    private readonly ILogger<MlImageProcessingHttpClient> _logger;

    public MlImageProcessingHttpClient(
        HttpClient httpClient,
        IOptions<MlServiceOptions> options,
        ILogger<MlImageProcessingHttpClient> logger)
    {
        _httpClient = httpClient;
        _options = options.Value;
        _logger = logger;
    }

    public Task<ImageContent> PreprocessBoardAsync(
        ImageContent image,
        CancellationToken cancellationToken = default)
    {
        return SendImageAsync(_options.PreprocessBoardPath, image, cancellationToken);
    }

    public Task<CellsGrid> ExtractCellsAsync(
        ImageContent image,
        CancellationToken cancellationToken = default)
    {
        return SendCellsAsync(_options.PreprocessCellsPath, image, cancellationToken);
    }

    public async Task<InferSudokuCellDigitMlResultDto> InferDigitAsync(
        InferSudokuCellDigitMlRequestDto request,
        CancellationToken cancellationToken = default)
    {
        var payload = await SendInferDigitAsync(_options.CellInferencePath, request, cancellationToken);

        if (payload.Digit is < 1 or > 9)
        {
            throw new MlOperationFailedException(
                InferSudokuCellDigitErrorTypes.MlInvalidResponse,
                "Serwis ML zwrócił cyfrę spoza dozwolonego zakresu 1..9 albo null.");
        }

        return new InferSudokuCellDigitMlResultDto(payload.Digit);
    }

    private async Task<ImageContent> SendImageAsync(
        string relativePath,
        ImageContent image,
        CancellationToken cancellationToken)
    {
        var payload = await SendAsync<ImageApiContract>(relativePath, image, cancellationToken);
        return ToImageContent(payload);
    }

    private async Task<CellsGrid> SendCellsAsync(
        string relativePath,
        ImageContent image,
        CancellationToken cancellationToken)
    {
        var payload = await SendAsync<CellsGridApiContract>(relativePath, image, cancellationToken);
        if (payload.Cells is null)
        {
            throw new MlOperationFailedException(
                DefaultOperationErrorType,
                "Serwis ML zwrócił nieprawidłową strukturę odpowiedzi dla siatki komórek.");
        }

        var mappedRows = new List<IReadOnlyList<ImageContent>>(payload.Cells.Count);
        for (var rowIndex = 0; rowIndex < payload.Cells.Count; rowIndex++)
        {
            var row = payload.Cells[rowIndex];
            if (row is null)
            {
                throw new MlOperationFailedException(
                    DefaultOperationErrorType,
                    $"Serwis ML zwrócił nieprawidłową strukturę odpowiedzi dla wiersza {rowIndex} siatki komórek.");
            }

            var mappedColumns = new ImageContent[row.Count];
            for (var columnIndex = 0; columnIndex < row.Count; columnIndex++)
            {
                mappedColumns[columnIndex] = ToImageContent(row[columnIndex]);
            }

            mappedRows.Add(mappedColumns);
        }

        try
        {
            return new CellsGrid(mappedRows);
        }
        catch (ArgumentException exception)
        {
            throw new MlOperationFailedException(
                DefaultOperationErrorType,
                exception.Message);
        }
    }

    private Task<DigitInferenceApiContract> SendInferDigitAsync(
        string relativePath,
        InferSudokuCellDigitMlRequestDto request,
        CancellationToken cancellationToken)
    {
        var payload = new DigitInferenceRequestApiContract(
            Image: new ImageApiContract(
                MimeType: request.Image.MimeType,
                Base64: Convert.ToBase64String(request.Image.Content)),
            ActiveModel: new DigitInferenceActiveModelApiContract(
                Name: request.ActiveModel.Name,
                ManifestPath: request.ActiveModel.ManifestPath,
                PrimaryArtifactPath: request.ActiveModel.PrimaryArtifactPath,
                InputProfile: request.ActiveModel.InputProfile),
            ResolvedConfiguration: new DigitInferenceResolvedConfigurationApiContract(
                InferenceProfileName: request.ResolvedConfiguration.InferenceProfileName,
                EmptyCellInnerMarginRatio: request.ResolvedConfiguration.EmptyCellInnerMarginRatio,
                EmptyCellDarkPixelRatioThreshold: request.ResolvedConfiguration.EmptyCellDarkPixelRatioThreshold,
                CenterAreaRatio: request.ResolvedConfiguration.CenterAreaRatio,
                MinComponentAreaRatio: request.ResolvedConfiguration.MinComponentAreaRatio,
                LineArtifactMinSpanRatio: request.ResolvedConfiguration.LineArtifactMinSpanRatio,
                LineArtifactMaxThicknessRatio: request.ResolvedConfiguration.LineArtifactMaxThicknessRatio
            ));

        return SendPayloadAsync<DigitInferenceRequestApiContract, DigitInferenceApiContract>(
            relativePath,
            payload,
            cancellationToken);
    }

    private async Task<TResponse> SendAsync<TResponse>(
        string relativePath,
        ImageContent image,
        CancellationToken cancellationToken)
    {
        var payload = new ImageApiContract(
            MimeType: image.MimeType,
            Base64: Convert.ToBase64String(image.Content));

        return await SendPayloadAsync<ImageApiContract, TResponse>(
            relativePath,
            payload,
            cancellationToken);
    }

    private async Task<TResponse> SendPayloadAsync<TRequest, TResponse>(
        string relativePath,
        TRequest payload,
        CancellationToken cancellationToken)
    {
        try
        {
            using var response = await _httpClient.PutAsJsonAsync(
                relativePath,
                payload,
                cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                await ThrowMappedExceptionAsync(response, cancellationToken);
            }

            var responsePayload = await response.Content.ReadFromJsonAsync<TResponse>(cancellationToken: cancellationToken);
            if (responsePayload is null)
            {
                throw new MlOperationFailedException(
                    DefaultOperationErrorType,
                    "Serwis ML zwrócił pustą odpowiedź.");
            }

            return responsePayload;
        }
        catch (OperationCanceledException exception) when (!cancellationToken.IsCancellationRequested)
        {
            _logger.LogError(exception, "Wywołanie ML pod ścieżką {RelativePath} przekroczyło timeout.", relativePath);
            throw new MlServiceTimeoutException("Upłynął limit czasu odpowiedzi serwisu ML.");
        }
        catch (HttpRequestException exception)
        {
            _logger.LogError(exception, "Wywołanie ML pod ścieżką {RelativePath} zakończyło się błędem sieci.", relativePath);
            throw new MlServiceUnavailableException("Serwis ML jest niedostępny.");
        }
        catch (JsonException exception)
        {
            _logger.LogError(exception, "Serwis ML zwrócił niepoprawny JSON pod ścieżką {RelativePath}.", relativePath);
            throw new MlOperationFailedException(
                DefaultOperationErrorType,
                "Serwis ML zwrócił nieprawidłowy payload JSON.");
        }
        catch (NotSupportedException exception)
        {
            _logger.LogError(exception, "Serwis ML zwrócił nieobsługiwany format JSON pod ścieżką {RelativePath}.", relativePath);
            throw new MlOperationFailedException(
                DefaultOperationErrorType,
                "Serwis ML zwrócił odpowiedź w nieobsługiwanym formacie.");
        }
    }

    private async Task ThrowMappedExceptionAsync(HttpResponseMessage response, CancellationToken cancellationToken)
    {
        var statusCode = response.StatusCode;
        var errorPayload = await TryReadErrorPayloadAsync(response, cancellationToken);
        var message = ResolveErrorMessage(errorPayload, statusCode);

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

    private static string ResolveErrorMessage(ErrorApiContract? errorPayload, HttpStatusCode statusCode)
    {
        if (!string.IsNullOrWhiteSpace(errorPayload?.Message))
        {
            return errorPayload.Message;
        }

        return $"Serwis ML zwrócił status HTTP {(int)statusCode}.";
    }

    private static async Task<ErrorApiContract?> TryReadErrorPayloadAsync(
        HttpResponseMessage response,
        CancellationToken cancellationToken)
    {
        try
        {
            return await response.Content.ReadFromJsonAsync<ErrorApiContract>(cancellationToken: cancellationToken);
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

    private static ImageContent ToImageContent(ImageApiContract? payload)
    {
        if (payload is null)
        {
            throw new MlOperationFailedException(
                DefaultOperationErrorType,
                "Serwis ML zwrócił pusty payload obrazu.");
        }

        if (string.IsNullOrWhiteSpace(payload.MimeType))
        {
            throw new MlOperationFailedException(
                DefaultOperationErrorType,
                "Serwis ML zwrócił obraz bez pola mimeType.");
        }

        if (string.IsNullOrWhiteSpace(payload.Base64))
        {
            throw new MlOperationFailedException(
                DefaultOperationErrorType,
                "Serwis ML zwrócił obraz bez pola base64.");
        }

        try
        {
            return new ImageContent(
                MimeType: payload.MimeType,
                Content: Convert.FromBase64String(payload.Base64));
        }
        catch (FormatException)
        {
            throw new MlOperationFailedException(
                DefaultOperationErrorType,
                "Serwis ML zwrócił obraz z nieprawidłowym base64.");
        }
    }

    private sealed record ImageApiContract(
        string? MimeType,
        string? Base64);

    private sealed record CellsGridApiContract(
        IReadOnlyList<IReadOnlyList<ImageApiContract?>?>? Cells);

    private sealed record DigitInferenceRequestApiContract(
        ImageApiContract Image,
        DigitInferenceActiveModelApiContract ActiveModel,
        DigitInferenceResolvedConfigurationApiContract ResolvedConfiguration);

    private sealed record DigitInferenceActiveModelApiContract(
        string Name,
        string ManifestPath,
        string PrimaryArtifactPath,
        string InputProfile);

    private sealed record DigitInferenceResolvedConfigurationApiContract(
        string InferenceProfileName,
        double EmptyCellInnerMarginRatio,
        double EmptyCellDarkPixelRatioThreshold,
        double CenterAreaRatio,
        double MinComponentAreaRatio,
        double LineArtifactMinSpanRatio,
        double LineArtifactMaxThicknessRatio
    );

    private sealed record DigitInferenceApiContract(int? Digit);

    private sealed record ErrorApiContract(
        string? ErrorType,
        string? Message);
}
