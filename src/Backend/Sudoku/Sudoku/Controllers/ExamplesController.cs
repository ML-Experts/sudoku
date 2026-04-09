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
            return MapValidationError(exception, UploadExampleErrorTypes.InvalidRequest);
        }
        catch (FileStorageConflictException exception)
        {
            return Conflict(new ErrorApiResponse(
                ErrorType: UploadExampleErrorTypes.ExampleConflict,
                Message: exception.Message));
        }
    }

    private IActionResult MapValidationError(ValidationException exception, string defaultErrorType)
    {
        var failure = exception.Errors.FirstOrDefault();
        var errorType = failure?.ErrorCode ?? defaultErrorType;
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
}
