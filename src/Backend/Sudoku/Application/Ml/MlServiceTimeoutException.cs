namespace Sudoku.Application.Ml;

public sealed class MlServiceTimeoutException : Exception
{
    public MlServiceTimeoutException(string message)
        : base(message)
    {
    }
}
