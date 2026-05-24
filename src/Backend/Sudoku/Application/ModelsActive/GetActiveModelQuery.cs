using MediatR;

namespace Sudoku.Application.ModelsActive;

public sealed record GetActiveModelQuery : IRequest<GetActiveModelQueryResultDto>;
