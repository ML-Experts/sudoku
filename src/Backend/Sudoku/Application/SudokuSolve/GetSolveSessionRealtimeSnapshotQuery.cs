using MediatR;

namespace Sudoku.Application.SudokuSolve;

public sealed record GetSolveSessionRealtimeSnapshotQuery(
    string? SolveSessionId) : IRequest<GetSolveSessionRealtimeSnapshotResultDto>;
