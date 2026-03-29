namespace Sudoku.Application.Ping;

public sealed record PingResultDto(
    bool IsMlAvailable,
    DateTimeOffset TimestampUtc,
    string Message);
