using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Text.Json;
using Sudoku.Application.Datasets;
using Sudoku.Application.Ml;
using Sudoku.Application.Storage;
using Sudoku.Contracts;

namespace Sudoku.Controllers;

[ApiController]
[Route("api/datasets")]
public sealed class DatasetsController : ControllerBase
{
    private readonly ISender _sender;

    public DatasetsController(ISender sender)
    {
        _sender = sender;
    }

    [Authorize]
    [HttpGet("raw-candidates")]
    [ProducesResponseType(typeof(IReadOnlyList<RawDatasetCandidateApiResponse>), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> ListRawCandidatesAsync(CancellationToken cancellationToken)
    {
        try
        {
            var result = await _sender.Send(new ListRawDatasetCandidatesQuery(), cancellationToken);
            var response = result.Items
                .Select(item => new RawDatasetCandidateApiResponse(
                    Name: item.Name,
                    Type: item.Type))
                .ToArray();

            return Ok(response);
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException)
        {
            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: ListRawDatasetCandidatesErrorTypes.ScanFailed,
                    Message: "Nie udało się odczytać kandydatów datasetów z katalogu źródłowego."));
        }
    }

    [Authorize]
    [HttpPost("processed")]
    [ProducesResponseType(typeof(ProcessedDatasetApiResponse), StatusCodes.Status201Created)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status404NotFound)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status409Conflict)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status422UnprocessableEntity)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status503ServiceUnavailable)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status504GatewayTimeout)]
    public async Task<IActionResult> CreateProcessedAsync(
        [FromBody] CreateProcessedDatasetApiEntry? entry,
        CancellationToken cancellationToken)
    {
        var command = new CreateProcessedDatasetCommand(
            Name: entry?.Name,
            Sources: entry?.Sources
                ?.Select(source => new SelectedRawDatasetSourceDto(
                    Name: source.Name,
                    Type: source.Type,
                    Splits: source.Splits))
                .ToArray());

        try
        {
            var result = await _sender.Send(command, cancellationToken);
            return StatusCode(StatusCodes.Status201Created, ToProcessedDatasetApiResponse(result));
        }
        catch (ValidationException exception)
        {
            return MapValidationError(exception);
        }
        catch (RawDatasetNotFoundException exception)
        {
            return NotFound(new ErrorApiResponse(
                ErrorType: CreateProcessedDatasetErrorTypes.RawDatasetNotFound,
                Message: exception.Message));
        }
        catch (RawDatasetTypeMismatchException exception)
        {
            return UnprocessableEntity(new ErrorApiResponse(
                ErrorType: CreateProcessedDatasetErrorTypes.RawDatasetTypeMismatch,
                Message: exception.Message));
        }
        catch (NoSamplesPreparedException exception)
        {
            return UnprocessableEntity(new ErrorApiResponse(
                ErrorType: CreateProcessedDatasetErrorTypes.NoSamplesPrepared,
                Message: exception.Message));
        }
        catch (FileStorageConflictException exception)
        {
            return Conflict(new ErrorApiResponse(
                ErrorType: CreateProcessedDatasetErrorTypes.ProcessedDatasetNameConflict,
                Message: exception.Message));
        }
        catch (FileStorageItemNotFoundException exception)
        {
            return StatusCode(
                StatusCodes.Status503ServiceUnavailable,
                new ErrorApiResponse(
                    ErrorType: CreateProcessedDatasetErrorTypes.ArtifactPromotionFailed,
                    Message: exception.Message));
        }
        catch (MlOperationFailedException exception)
        {
            return UnprocessableEntity(new ErrorApiResponse(
                ErrorType: exception.ErrorType,
                Message: exception.Message));
        }
        catch (MlServiceUnavailableException exception)
        {
            return StatusCode(
                StatusCodes.Status503ServiceUnavailable,
                new ErrorApiResponse(
                    ErrorType: CreateProcessedDatasetErrorTypes.MlUnavailable,
                    Message: exception.Message));
        }
        catch (MlServiceTimeoutException exception)
        {
            return StatusCode(
                StatusCodes.Status504GatewayTimeout,
                new ErrorApiResponse(
                    ErrorType: CreateProcessedDatasetErrorTypes.MlTimeout,
                    Message: exception.Message));
        }
    }

    [Authorize]
    [HttpGet("processed")]
    [ProducesResponseType(typeof(ProcessedDatasetsListApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> ListProcessedAsync(CancellationToken cancellationToken)
    {
        try
        {
            var result = await _sender.Send(new ListProcessedDatasetsQuery(), cancellationToken);
            var items = result.Items
                .Select(item => new ProcessedDatasetListItemApiResponse(
                    Name: item.Name,
                    FileName: item.FileName,
                    PreprocessingProfile: item.PreprocessingProfile,
                    CreatedAtUtc: item.CreatedAtUtc,
                    SampleCounts: new SplitSampleCountsApiResponse(
                        Train: item.SampleCounts.Train,
                        Val: item.SampleCounts.Val,
                        Test: item.SampleCounts.Test)))
                .ToArray();

            return Ok(new ProcessedDatasetsListApiResponse(
                Items: items,
                TotalCount: result.TotalCount));
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidDataException
                                         or JsonException
                                         or FileStorageItemNotFoundException)
        {
            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new ErrorApiResponse(
                    ErrorType: ListProcessedDatasetsErrorTypes.ReadFailed,
                    Message: "Nie udało się odczytać listy przygotowanych datasetów."));
        }
    }

    private static ProcessedDatasetApiResponse ToProcessedDatasetApiResponse(
        CreateProcessedDatasetCommandResultDto result)
    {
        return new ProcessedDatasetApiResponse(
            Name: result.Name,
            FileName: result.FileName,
            PreprocessingProfile: result.PreprocessingProfile,
            CreatedAtUtc: result.CreatedAtUtc,
            Sources: result.Sources
                .Select(source => new SelectedRawDatasetSourceApiEntry(
                    Name: source.Name,
                    Type: source.Type,
                    Splits: source.Splits))
                .ToArray(),
            SampleCounts: new SplitSampleCountsApiResponse(
                Train: result.SampleCounts.Train,
                Val: result.SampleCounts.Val,
                Test: result.SampleCounts.Test),
            SourceReports: result.SourceReports
                .Select(report => new ProcessedDatasetSourceReportApiResponse(
                    Name: report.Name,
                    Type: report.Type,
                    ProcessedSampleCount: report.ProcessedSampleCount,
                    IncludedSampleCount: report.IncludedSampleCount,
                    EmptyCellCount: report.EmptyCellCount,
                    RejectedSampleCount: report.RejectedSampleCount,
                    Warnings: report.Warnings))
                .ToArray(),
            Warnings: result.Warnings);
    }

    private static IActionResult MapValidationError(ValidationException exception)
    {
        var failure = exception.Errors.FirstOrDefault();
        var errorType = failure?.ErrorCode ?? CreateProcessedDatasetErrorTypes.InvalidRequest;
        var message = failure?.ErrorMessage ?? "Nieprawidłowe dane wejściowe.";
        var statusCode = errorType switch
        {
            CreateProcessedDatasetErrorTypes.InvalidDatasetSplitSelection => StatusCodes.Status400BadRequest,
            _ => StatusCodes.Status400BadRequest
        };

        return new ObjectResult(new ErrorApiResponse(
            ErrorType: errorType,
            Message: message))
        {
            StatusCode = statusCode
        };
    }
}
