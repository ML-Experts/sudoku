namespace Sudoku.Application.Ml;

public sealed class MlServiceUnavailableException : Exception
{
    public MlServiceUnavailableException(string message)
        : base(message)
    {
    }
}
