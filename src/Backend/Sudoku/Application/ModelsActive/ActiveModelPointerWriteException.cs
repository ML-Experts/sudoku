namespace Sudoku.Application.ModelsActive;

public sealed class ActiveModelPointerWriteException : Exception
{
    public ActiveModelPointerWriteException(string modelName, string message, Exception innerException)
        : base(message, innerException)
    {
        ModelName = modelName;
    }

    public string ModelName { get; }
}
