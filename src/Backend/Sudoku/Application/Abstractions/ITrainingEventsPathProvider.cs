namespace Sudoku.Application.Abstractions;

public interface ITrainingEventsPathProvider
{
    string GetEventsPath(string runName);
}
