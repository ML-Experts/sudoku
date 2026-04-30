using Sudoku.Application.Trainings;

namespace Sudoku.Application.Abstractions;

public interface ITrainingRunEventPublisher
{
    Task PublishAsync(
        TrainingRunMetadataDto metadata,
        CancellationToken cancellationToken = default);
}
