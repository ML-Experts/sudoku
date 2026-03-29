using MediatR;
using Sudoku.Application.Abstractions;

namespace Sudoku.Application.Ping;

public sealed class GetPingQueryHandler : IRequestHandler<GetPingQuery, PingResultDto>
{
    private readonly IMlPingGateway _mlPingGateway;
    private readonly TimeProvider _timeProvider;

    public GetPingQueryHandler(IMlPingGateway mlPingGateway, TimeProvider timeProvider)
    {
        _mlPingGateway = mlPingGateway;
        _timeProvider = timeProvider;
    }

    public async Task<PingResultDto> Handle(GetPingQuery request, CancellationToken cancellationToken)
    {
        var mlPingResult = await _mlPingGateway.PingAsync(cancellationToken);

        return new PingResultDto(
            IsMlAvailable: mlPingResult.IsAvailable,
            TimestampUtc: _timeProvider.GetUtcNow(),
            Message: $"Backend responded successfully. {mlPingResult.Message}");
    }
}
