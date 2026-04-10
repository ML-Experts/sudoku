using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using Sudoku.Application.Examples;
using Sudoku.Application.Ml;
using Sudoku.Application.Storage;
using Sudoku.Contracts;

namespace Sudoku.Controllers;

[ApiController]
[Route("api/examples")]
public sealed class ExamplesController : ControllerBase
{
    private readonly ISender _sender;

    public ExamplesController(ISender sender)
    {
        _sender = sender;
    }

    [HttpGet("{name}")]
    [ProducesResponseType(typeof(ImageApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetByNameAsync(
        [FromRoute] string name,
        CancellationToken cancellationToken)
    {
        var query = new GetExampleImageQuery(Name: name);

        try
        {
            var result = await _sender.Send(query, cancellationToken);
            return Ok(new ImageApiResponse(
                MimeType: result.MimeType,
                Base64: result.Base64));
        }
        catch (ValidationException exception)
        {
            return MapValidationError(exception, GetExampleImageErrorTypes.InvalidRequest);
        }
        catch (FileStorageItemNotFoundException exception)
        {
            return NotFound(new ErrorApiResponse(
                ErrorType: GetExampleImageErrorTypes.ExampleNotFound,
                Message: exception.Message));
        }
    }

    [HttpPut("{name}/preprocess/board")]
    [ProducesResponseType(typeof(ImageApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status404NotFound)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status422UnprocessableEntity)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status503ServiceUnavailable)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status504GatewayTimeout)]
    public async Task<IActionResult> PreprocessBoardAsync(
        [FromRoute] string name,
        CancellationToken cancellationToken)
    {
        var command = new PreprocessExampleBoardCommand(Name: name);

        try
        {
            var result = await _sender.Send(command, cancellationToken);
            return Ok(new ImageApiResponse(
                MimeType: result.MimeType,
                Base64: result.Base64));
        }
        catch (ValidationException exception)
        {
            return MapValidationError(exception, PreprocessExampleBoardErrorTypes.InvalidRequest);
        }
        catch (FileStorageItemNotFoundException exception)
        {
            return NotFound(new ErrorApiResponse(
                ErrorType: PreprocessExampleBoardErrorTypes.ExampleNotFound,
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
                    ErrorType: PreprocessExampleBoardErrorTypes.MlUnavailable,
                    Message: exception.Message));
        }
        catch (MlServiceTimeoutException exception)
        {
            return StatusCode(
                StatusCodes.Status504GatewayTimeout,
                new ErrorApiResponse(
                    ErrorType: PreprocessExampleBoardErrorTypes.MlTimeout,
                    Message: exception.Message));
        }
    }

    [HttpPut("preprocess/cells")]
    [ProducesResponseType(typeof(CellsGridApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status422UnprocessableEntity)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status503ServiceUnavailable)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status504GatewayTimeout)]
    public async Task<IActionResult> PreprocessCellsAsync(
        [FromBody] ImageApiEntry? entry,
        CancellationToken cancellationToken)
    {
        var command = new PreprocessExampleCellsCommand(
            MimeType: entry?.MimeType,
            Base64: entry?.Base64);

        try
        {
            var result = await _sender.Send(command, cancellationToken);
            return Ok(ToCellsGridApiResponse(result));
        }
        catch (ValidationException exception)
        {
            return MapValidationError(exception, PreprocessExampleCellsErrorTypes.InvalidRequest);
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
                    ErrorType: PreprocessExampleCellsErrorTypes.MlUnavailable,
                    Message: exception.Message));
        }
        catch (MlServiceTimeoutException exception)
        {
            return StatusCode(
                StatusCodes.Status504GatewayTimeout,
                new ErrorApiResponse(
                    ErrorType: PreprocessExampleCellsErrorTypes.MlTimeout,
                    Message: exception.Message));
        }
    }

    [HttpGet]
    [ProducesResponseType(typeof(ExamplesListApiResponse), StatusCodes.Status200OK)]
    public async Task<IActionResult> ListAsync(CancellationToken cancellationToken)
    {
        var result = await _sender.Send(new ListExamplesQuery(), cancellationToken);
        var items = result.Items
            .Select(item => new ExampleFileApiResponse(
                Name: item.Name,
                ContentType: item.ContentType,
                SizeBytes: item.SizeBytes,
                StoredAtUtc: item.StoredAtUtc))
            .ToArray();

        var response = new ExamplesListApiResponse(
            Items: items,
            TotalCount: result.TotalCount);

        return Ok(response);
    }

    [HttpPost]
    [Consumes("multipart/form-data")]
    [ProducesResponseType(typeof(ExampleFileApiResponse), StatusCodes.Status201Created)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status409Conflict)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status413PayloadTooLarge)]
    [ProducesResponseType(typeof(ErrorApiResponse), StatusCodes.Status415UnsupportedMediaType)]
    public async Task<IActionResult> UploadAsync(
        [FromForm] UploadExampleApiEntry entry,
        CancellationToken cancellationToken)
    {
        using var stream = entry.File?.OpenReadStream();
        var command = new UploadExampleCommand(
            FileStream: stream,
            ContentType: entry.File?.ContentType,
            SizeBytes: entry.File?.Length);

        try
        {
            var result = await _sender.Send(command, cancellationToken);
            var response = new ExampleFileApiResponse(
                Name: result.Name,
                ContentType: result.ContentType,
                SizeBytes: result.SizeBytes,
                StoredAtUtc: result.StoredAtUtc);

            return StatusCode(StatusCodes.Status201Created, response);
        }
        catch (ValidationException exception)
        {
            return MapValidationError(exception);
        }
        catch (FileStorageConflictException exception)
        {
            return Conflict(new ErrorApiResponse(
                ErrorType: UploadExampleErrorTypes.ExampleConflict,
                Message: exception.Message));
        }
    }

    private IActionResult MapValidationError(ValidationException exception, string? defaultErrorType = null)
    {
        var failure = exception.Errors.FirstOrDefault();
        var errorType = failure?.ErrorCode ?? defaultErrorType ?? UploadExampleErrorTypes.InvalidRequest;
        var message = failure?.ErrorMessage ?? "Nieprawidłowe dane wejściowe.";
        var statusCode = errorType switch
        {
            UploadExampleErrorTypes.PayloadTooLarge => StatusCodes.Status413PayloadTooLarge,
            UploadExampleErrorTypes.UnsupportedMediaType => StatusCodes.Status415UnsupportedMediaType,
            _ => StatusCodes.Status400BadRequest
        };

        return StatusCode(
            statusCode,
            new ErrorApiResponse(
                ErrorType: errorType,
                Message: message));
    }

    private static CellsGridApiResponse ToCellsGridApiResponse(PreprocessCellsResultDto result)
    {
        var rows = result.Cells.Cells
            .Select(row => (IReadOnlyList<ImageApiResponse>)row
                .Select(cell => new ImageApiResponse(
                    MimeType: cell.MimeType,
                    Base64: Convert.ToBase64String(cell.Content)))
                .ToArray())
            .ToArray();

        return new CellsGridApiResponse(Cells: rows);
    }
}
