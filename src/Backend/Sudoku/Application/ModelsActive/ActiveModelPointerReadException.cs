namespace Sudoku.Application.ModelsActive;

public sealed class ActiveModelPointerReadException : Exception
{
    public ActiveModelPointerReadException(string message, Exception innerException)
        : base(message, innerException)
    {
    }
}
