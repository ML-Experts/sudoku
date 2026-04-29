namespace Sudoku.Contracts;

public sealed record CancelTrainingRunApiResponse(
    string RunName,
    string? Status,
    string RequestDisposition,
    string Message,
    string? ProgressChannelUrl);
