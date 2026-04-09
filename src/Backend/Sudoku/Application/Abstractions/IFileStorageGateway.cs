namespace Sudoku.Application.Abstractions;

public interface IFileStorageGateway
{
    Task SaveAsync(
        string directoryPath,
        string fileName,
        Stream content,
        CancellationToken cancellationToken = default);

    Task<Stream> OpenReadAsync(
        string directoryPath,
        string fileName,
        CancellationToken cancellationToken = default);
}
