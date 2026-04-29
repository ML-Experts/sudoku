using Sudoku.Application.Trainings;

namespace Sudoku.Application.Abstractions;

public interface ITrainingRunsGateway
{
    Task<IReadOnlyList<TrainingRunMetadataDto>> ListAsync(
        CancellationToken cancellationToken = default);

    Task<TrainingRunMetadataDto?> GetByRunNameAsync(
        string runName,
        CancellationToken cancellationToken = default);

    Task<bool> TryCreateAsync(
        TrainingRunMetadataDto metadata,
        CancellationToken cancellationToken = default);

    Task UpdateAsync(
        TrainingRunMetadataDto metadata,
        CancellationToken cancellationToken = default);

    Task DeleteAsync(
        string runName,
        CancellationToken cancellationToken = default);
}
