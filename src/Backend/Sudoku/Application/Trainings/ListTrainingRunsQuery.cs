using MediatR;

namespace Sudoku.Application.Trainings;

public sealed record ListTrainingRunsQuery : IRequest<ListTrainingRunsQueryResultDto>;
