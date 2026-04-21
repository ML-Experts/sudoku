using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Sudoku.Application.Datasets;
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
}
