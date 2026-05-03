using MediatR;

namespace Sudoku.Application.Trainings;

public sealed record RecordTrainingRunEventCommand(
    string? RunName,
    long Sequence,
    string? EventType,
    string? Status,
    string? Stage,
    DateTimeOffset OccurredAtUtc,
    string? Message,
    TrainingRunProgressDto? Progress,
    TrainingRunEventResultDto? Result,
    TrainingRunFailureDto? Failure,
    IReadOnlyList<string>? Warnings) : IRequest<RecordTrainingRunEventResultDto>;

public sealed record TrainingRunFailureDto(
    string? ErrorType,
    string? Message,
    bool? CanUseProducedModelForInference);
