namespace Sudoku.Contracts;

public sealed record PingApiResponse(
    string BackendStatus,
    string MlStatus,
    DateTimeOffset TimestampUtc,
    string Message);
