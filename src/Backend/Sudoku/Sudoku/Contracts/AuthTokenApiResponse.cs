namespace Sudoku.Contracts;

public sealed record AuthTokenApiResponse(
    string AccessToken,
    string TokenType,
    string ExpiresAtUtc);
