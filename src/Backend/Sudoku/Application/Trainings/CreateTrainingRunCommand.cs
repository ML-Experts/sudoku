using MediatR;

namespace Sudoku.Application.Trainings;

public sealed record CreateTrainingRunCommand(
    string? BaseModelName,
    string? ProcessedDatasetName,
    TrainingRunRequestedParametersDto? TrainingParameters) : IRequest<CreateTrainingRunCommandResultDto>;
