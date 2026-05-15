using System.Text.Json;
using MediatR;

namespace Sudoku.Application.SudokuSolve;

public sealed record StartSudokuSolveCommand(
    JsonElement? Grid) : IRequest<StartSudokuSolveCommandResultDto>;
