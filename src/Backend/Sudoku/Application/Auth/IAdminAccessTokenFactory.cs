namespace Sudoku.Application.Auth;

public interface IAdminAccessTokenFactory
{
    LoginCommandResultDto CreateToken(DateTimeOffset issuedAtUtc);
}
