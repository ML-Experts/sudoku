using MediatR;

namespace Sudoku.Application.Trainings;

public sealed record GetTrainingRunDetailsQuery(string? RunName)
    : IRequest<GetTrainingRunDetailsQueryResultDto>;

public sealed record GetTrainingRunDetailsQueryResultDto(
    TrainingRunDetailsDto Details);
