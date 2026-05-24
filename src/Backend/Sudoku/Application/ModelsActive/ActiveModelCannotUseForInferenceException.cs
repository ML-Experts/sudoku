namespace Sudoku.Application.ModelsActive;

public sealed class ActiveModelCannotUseForInferenceException : Exception
{
    public ActiveModelCannotUseForInferenceException(string modelName)
        : base($"Model {modelName} nie może zostać użyty do inferencji.")
    {
        ModelName = modelName;
    }

    public string ModelName { get; }
}
