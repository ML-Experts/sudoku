namespace Sudoku.Application.Auth;

public static class AdminAuthErrorTypes
{
    public const string InvalidRequest = "invalid_request";
    public const string InvalidCredentials = "invalid_credentials";
    public const string AdminTokenInvalid = "admin_token_invalid";
    public const string AdminTokenExpired = "admin_token_expired";
}
