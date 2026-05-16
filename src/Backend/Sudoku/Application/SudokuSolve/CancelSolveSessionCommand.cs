using MediatR;

namespace Sudoku.Application.SudokuSolve;

public sealed record CancelSolveSessionCommand(
    string? SolveSessionId) : IRequest<CancelSolveSessionCommandResultDto>;
