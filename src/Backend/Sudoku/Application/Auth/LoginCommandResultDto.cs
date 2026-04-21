namespace Sudoku.Application.Auth;

public sealed record LoginCommandResultDto(
    string AccessToken,
    string TokenType,
    DateTimeOffset ExpiresAtUtc);
