using MediatR;

namespace Sudoku.Application.Auth;

public sealed record LoginCommand(string? Password) : IRequest<LoginCommandResultDto>;
