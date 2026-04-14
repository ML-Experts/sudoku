namespace Sudoku.Application.Auth;

public sealed class InvalidAdminCredentialsException : Exception
{
    public InvalidAdminCredentialsException(string message)
        : base(message)
    {
    }
}
