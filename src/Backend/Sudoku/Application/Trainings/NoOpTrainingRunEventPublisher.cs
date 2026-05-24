using Sudoku.Application.Abstractions;

namespace Sudoku.Application.Trainings;

public sealed class NoOpTrainingRunEventPublisher : ITrainingRunEventPublisher
{
    public Task PublishAsync(
        TrainingRunMetadataDto metadata,
        CancellationToken cancellationToken = default)
    {
        return Task.CompletedTask;
    }
}
