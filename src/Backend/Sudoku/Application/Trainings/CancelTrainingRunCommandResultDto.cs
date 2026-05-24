namespace Sudoku.Application.Trainings;

public sealed record CancelTrainingRunCommandResultDto(
    string RunName,
    string? Status,
    string RequestDisposition,
    string Message,
    string? ProgressChannelUrl);
