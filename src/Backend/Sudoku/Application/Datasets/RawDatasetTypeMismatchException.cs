namespace Sudoku.Application.Datasets;

public sealed class RawDatasetTypeMismatchException : Exception
{
    public RawDatasetTypeMismatchException(string message)
        : base(message)
    {
    }
}
