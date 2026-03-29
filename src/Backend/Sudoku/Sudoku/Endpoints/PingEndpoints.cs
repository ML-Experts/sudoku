using MediatR;
using Sudoku.Application.Ping;
using Sudoku.Contracts;

namespace Sudoku.Endpoints;

public static class PingEndpoints
{
    public static IEndpointRouteBuilder MapPingEndpoints(this IEndpointRouteBuilder endpoints)
    {
        endpoints.MapGet("/api/ping", HandleAsync)
            .WithName("Ping");

        return endpoints;
    }

    private static async Task<IResult> HandleAsync(ISender sender, CancellationToken cancellationToken)
    {
        var result = await sender.Send(new GetPingQuery(), cancellationToken);
        var response = new PingApiResponse(
            BackendStatus: "ok",
            MlStatus: result.IsMlAvailable ? "ok" : "unavailable",
            TimestampUtc: result.TimestampUtc,
            Message: result.Message);

        return result.IsMlAvailable
            ? Results.Ok(response)
            : Results.Json(response, statusCode: StatusCodes.Status503ServiceUnavailable);
    }
}
