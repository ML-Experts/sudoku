namespace Sudoku.Application.Trainings;

public sealed record CancelMlTrainingRequestDto(
    string RunName,
    DateTimeOffset RequestedAtUtc,
    string Reason);
