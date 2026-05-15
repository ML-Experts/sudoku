using MediatR;

namespace Sudoku.Application.SudokuSolve;

public sealed record GetActiveSolveSessionQuery() : IRequest<GetActiveSolveSessionQueryResultDto>;
