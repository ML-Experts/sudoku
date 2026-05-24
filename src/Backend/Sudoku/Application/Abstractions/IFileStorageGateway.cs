using Sudoku.Application.Storage;

namespace Sudoku.Application.Abstractions;

public interface IFileStorageGateway
{
    Task SaveAsync(
        string directoryPath,
        string fileName,
        Stream content,
        CancellationToken cancellationToken = default);

    Task ReplaceAsync(
        string directoryPath,
        string fileName,
        Stream content,
        CancellationToken cancellationToken = default);

    Task DeleteAsync(
        string directoryPath,
        string fileName,
        CancellationToken cancellationToken = default);

    Task DeleteDirectoryAsync(
        string directoryPath,
        string directoryName,
        CancellationToken cancellationToken = default);

    Task<Stream> OpenReadAsync(
        string directoryPath,
        string fileName,
        CancellationToken cancellationToken = default);

    Task<bool> FileExistsAsync(
        string directoryPath,
        string fileName,
        CancellationToken cancellationToken = default);

    Task<IReadOnlyList<StoredFileMetadataDto>> ListFilesAsync(
        string directoryPath,
        CancellationToken cancellationToken = default);

    Task<IReadOnlyList<StoredDirectoryMetadataDto>> ListDirectoriesAsync(
        string directoryPath,
        CancellationToken cancellationToken = default);
}
