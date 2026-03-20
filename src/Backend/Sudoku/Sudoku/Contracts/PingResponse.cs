namespace Sudoku.Contracts;

public sealed record PingResponse(
    string BackendStatus,
    string MlStatus,
    DateTimeOffset TimestampUtc,
    string Message);
