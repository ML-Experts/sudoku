namespace Sudoku.Models.Ping;

public sealed record MlPingResult(
    bool IsAvailable,
    int? StatusCode,
    string Message);
