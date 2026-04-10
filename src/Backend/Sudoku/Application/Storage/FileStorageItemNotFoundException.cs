namespace Sudoku.Application.Storage;

public sealed class FileStorageItemNotFoundException : Exception
{
    public FileStorageItemNotFoundException(string message)
        : base(message)
    {
    }
}
