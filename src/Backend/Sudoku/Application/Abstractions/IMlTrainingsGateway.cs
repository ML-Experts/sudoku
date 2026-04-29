using Sudoku.Application.Trainings;

namespace Sudoku.Application.Abstractions;

public interface IMlTrainingsGateway
{
    Task<StartMlTrainingResultDto> StartTrainingAsync(
        StartMlTrainingRequestDto request,
        CancellationToken cancellationToken = default);
}
