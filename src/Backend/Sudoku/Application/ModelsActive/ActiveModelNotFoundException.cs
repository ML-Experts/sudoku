namespace Sudoku.Application.ModelsActive;

public sealed class ActiveModelNotFoundException : Exception
{
    public ActiveModelNotFoundException(string modelName)
        : base($"Model {modelName} nie istnieje w rejestrze.")
    {
        ModelName = modelName;
    }

    public string ModelName { get; }
}
