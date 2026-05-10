namespace Sudoku.Application.ModelsActive;

public sealed class ActiveModelManifestInvalidException : Exception
{
    public ActiveModelManifestInvalidException(string modelName, string message)
        : base(message)
    {
        ModelName = modelName;
    }

    public ActiveModelManifestInvalidException(string modelName, string message, Exception innerException)
        : base(message, innerException)
    {
        ModelName = modelName;
    }

    public string ModelName { get; }
}
