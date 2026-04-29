using MediatR;

namespace Sudoku.Application.Trainings;

public sealed record CancelTrainingRunCommand(
    string? RunName) : IRequest<CancelTrainingRunCommandResultDto>;
