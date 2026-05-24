using MediatR;

namespace Sudoku.Application.Trainings;

public sealed record GetActiveTrainingRunQuery() : IRequest<GetActiveTrainingRunQueryResultDto>;
