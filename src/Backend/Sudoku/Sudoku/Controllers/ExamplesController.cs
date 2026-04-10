using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using Sudoku.Application.Examples;
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

    private IActionResult MapValidationError(ValidationException exception)
    {
        var failure = exception.Errors.FirstOrDefault();
        var errorType = failure?.ErrorCode ?? UploadExampleErrorTypes.InvalidRequest;
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
