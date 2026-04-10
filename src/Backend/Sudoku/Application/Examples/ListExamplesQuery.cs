using MediatR;

namespace Sudoku.Application.Examples;

public sealed record ListExamplesQuery : IRequest<ListExamplesQueryResultDto>;
