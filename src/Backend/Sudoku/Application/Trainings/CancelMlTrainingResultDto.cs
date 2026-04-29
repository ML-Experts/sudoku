namespace Sudoku.Application.Trainings;

public sealed record CancelMlTrainingResultDto(
    bool Accepted,
    string RunName,
    string? Status,
    string? Disposition);
