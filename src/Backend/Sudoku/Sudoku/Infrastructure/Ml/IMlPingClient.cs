using System.Net;

namespace Sudoku.Infrastructure.Ml;

public interface IMlPingClient
{
    Task<MlPingResult> PingAsync(CancellationToken cancellationToken = default);
}

public sealed record MlPingResult(
    bool IsAvailable,
    HttpStatusCode? StatusCode,
    string Message);
