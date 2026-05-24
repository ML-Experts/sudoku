using MediatR;

namespace Sudoku.Application.ModelsActive;

public sealed record SetActiveModelCommand(
    string? ModelName) : IRequest<SetActiveModelCommandResultDto>;
