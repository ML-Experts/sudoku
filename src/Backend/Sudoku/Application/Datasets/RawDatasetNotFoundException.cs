namespace Sudoku.Application.Datasets;

public sealed class RawDatasetNotFoundException : Exception
{
    public RawDatasetNotFoundException(string message)
        : base(message)
    {
    }
}
