using Sudoku.Application.Trainings;

namespace Sudoku.Application.Abstractions;

public interface ITrainingRunsGateway
{
    Task<IReadOnlyList<TrainingRunMetadataDto>> ListAsync(
        CancellationToken cancellationToken = default);
}
