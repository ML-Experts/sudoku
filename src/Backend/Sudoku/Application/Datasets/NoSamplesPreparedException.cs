namespace Sudoku.Application.Datasets;

public sealed class NoSamplesPreparedException : Exception
{
    public NoSamplesPreparedException(string message)
        : base(message)
    {
    }
}
