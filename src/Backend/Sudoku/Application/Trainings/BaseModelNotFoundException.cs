namespace Sudoku.Application.Trainings;

public sealed class BaseModelNotFoundException : Exception
{
    public BaseModelNotFoundException(string modelName)
        : base($"Model bazowy {modelName} nie został odnaleziony.")
    {
        ModelName = modelName;
    }

    public string ModelName { get; }
}
