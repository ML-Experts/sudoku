using Sudoku.Application.Trainings;

namespace Sudoku.Application.Abstractions;

public interface ITrainingArtifactsCleanupGateway
{
    Task<IReadOnlyList<string>> CleanupFailedOrCancelledRunAsync(
        TrainingRunMetadataDto metadata,
        CancellationToken cancellationToken = default);
}
