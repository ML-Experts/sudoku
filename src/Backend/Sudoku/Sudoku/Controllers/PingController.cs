using MediatR;
using Microsoft.AspNetCore.Mvc;
using Sudoku.Application.Ping;
using Sudoku.Contracts;

namespace Sudoku.Controllers;

[ApiController]
[Route("api/ping")]
public sealed class PingController : ControllerBase
{
    private readonly ISender _sender;

    public PingController(ISender sender)
    {
        _sender = sender;
    }

    [HttpGet]
    [ProducesResponseType(typeof(PingApiResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(PingApiResponse), StatusCodes.Status503ServiceUnavailable)]
    public async Task<IActionResult> GetAsync(CancellationToken cancellationToken)
    {
        var result = await _sender.Send(new GetPingQuery(), cancellationToken);
        var response = new PingApiResponse(
            BackendStatus: "ok",
            MlStatus: result.IsMlAvailable ? "ok" : "unavailable",
            TimestampUtc: result.TimestampUtc,
            Message: result.Message);

        return result.IsMlAvailable
            ? Ok(response)
            : StatusCode(StatusCodes.Status503ServiceUnavailable, response);
    }
}
