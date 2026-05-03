namespace Sudoku.Application.ModelsActive;

public sealed class ActiveModelPointerInvalidException : Exception
{
    public ActiveModelPointerInvalidException(string? modelName, string message)
        : base(message)
    {
        ModelName = modelName;
    }

    public ActiveModelPointerInvalidException(string? modelName, string message, Exception innerException)
        : base(message, innerException)
    {
        ModelName = modelName;
    }

    public string? ModelName { get; }
}
