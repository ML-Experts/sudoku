using Sudoku.Models.Ping;

namespace Sudoku.Application.Abstractions;

public interface IMlPingGateway
{
    Task<MlPingResult> PingAsync(CancellationToken cancellationToken = default);
}
