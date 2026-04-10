using MediatR;

namespace Sudoku.Application.Examples;

public sealed record GetExampleImageQuery(string? Name) : IRequest<GetExampleImageResultDto>;
