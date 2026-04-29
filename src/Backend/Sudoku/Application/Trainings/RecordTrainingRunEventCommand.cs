using MediatR;

namespace Sudoku.Application.Trainings;

public sealed record RecordTrainingRunEventCommand(
    string? RunName,
    long Sequence,
    string? EventType,
    string? Status,
    DateTimeOffset OccurredAtUtc,
    string? Message,
    TrainingRunProgressDto? Progress,
    TrainingRunEventResultDto? Result,
    IReadOnlyList<string>? Warnings) : IRequest<RecordTrainingRunEventResultDto>;
