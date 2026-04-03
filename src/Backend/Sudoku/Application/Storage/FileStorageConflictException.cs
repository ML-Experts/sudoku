namespace Sudoku.Application.Storage;

public sealed class FileStorageConflictException : Exception
{
    public FileStorageConflictException(string message)
        : base(message)
    {
    }
}
