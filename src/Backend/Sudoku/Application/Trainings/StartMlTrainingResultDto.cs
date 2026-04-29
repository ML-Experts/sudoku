namespace Sudoku.Application.Trainings;

public sealed record StartMlTrainingResultDto(
    DateTimeOffset? AcceptedAtUtc,
    string? MlJobId);
