namespace Sudoku.Application.Ml;

public sealed class MlOperationFailedException : Exception
{
    public MlOperationFailedException(string errorType, string message)
        : base(message)
    {
        ErrorType = errorType;
    }

    public string ErrorType { get; }
}
