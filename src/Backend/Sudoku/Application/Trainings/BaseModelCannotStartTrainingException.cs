namespace Sudoku.Application.Trainings;

public sealed class BaseModelCannotStartTrainingException : Exception
{
    public BaseModelCannotStartTrainingException(string modelName)
        : base($"Model bazowy {modelName} nie może zostać użyty do startu treningu.")
    {
        ModelName = modelName;
    }

    public string ModelName { get; }
}
