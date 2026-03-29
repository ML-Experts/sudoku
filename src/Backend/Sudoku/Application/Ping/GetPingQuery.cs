using MediatR;

namespace Sudoku.Application.Ping;

public sealed record GetPingQuery : IRequest<PingResultDto>;
