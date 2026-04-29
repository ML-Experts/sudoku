using Sudoku.Application.Abstractions;
using Sudoku.Application.Storage;

namespace Sudoku.Infrastructure.Storage;

public sealed class LocalFileStorageGateway : IFileStorageGateway
{
    public async Task SaveAsync(
        string directoryPath,
        string fileName,
        Stream content,
        CancellationToken cancellationToken = default)
    {
        var fullDirectoryPath = Path.GetFullPath(directoryPath);
        Directory.CreateDirectory(fullDirectoryPath);

        var targetPath = Path.GetFullPath(Path.Combine(fullDirectoryPath, fileName));
        EnsurePathIsWithinDirectory(fullDirectoryPath, targetPath);

        if (content.CanSeek)
        {
            content.Seek(0, SeekOrigin.Begin);
        }

        try
        {
            await using var targetStream = new FileStream(
                targetPath,
                FileMode.CreateNew,
                FileAccess.Write,
                FileShare.None,
                bufferSize: 81920,
                useAsync: true);

            await content.CopyToAsync(targetStream, cancellationToken);
        }
        catch (IOException) when (File.Exists(targetPath))
        {
            throw new FileStorageConflictException("Plik o tej nazwie już istnieje.");
        }
    }

    public async Task ReplaceAsync(
        string directoryPath,
        string fileName,
        Stream content,
        CancellationToken cancellationToken = default)
    {
        var fullDirectoryPath = Path.GetFullPath(directoryPath);
        Directory.CreateDirectory(fullDirectoryPath);

        var targetPath = Path.GetFullPath(Path.Combine(fullDirectoryPath, fileName));
        EnsurePathIsWithinDirectory(fullDirectoryPath, targetPath);

        if (content.CanSeek)
        {
            content.Seek(0, SeekOrigin.Begin);
        }

        var temporaryFileName = $".{fileName}.{Guid.NewGuid():N}.tmp";
        var temporaryPath = Path.GetFullPath(Path.Combine(fullDirectoryPath, temporaryFileName));
        EnsurePathIsWithinDirectory(fullDirectoryPath, temporaryPath);

        try
        {
            await using (var targetStream = new FileStream(
                             temporaryPath,
                             FileMode.CreateNew,
                             FileAccess.Write,
                             FileShare.None,
                             bufferSize: 81920,
                             useAsync: true))
            {
                await content.CopyToAsync(targetStream, cancellationToken);
            }

            File.Move(temporaryPath, targetPath, overwrite: true);
        }
        finally
        {
            if (File.Exists(temporaryPath))
            {
                File.Delete(temporaryPath);
            }
        }
    }

    public Task DeleteAsync(
        string directoryPath,
        string fileName,
        CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var fullDirectoryPath = Path.GetFullPath(directoryPath);
        var targetPath = Path.GetFullPath(Path.Combine(fullDirectoryPath, fileName));
        EnsurePathIsWithinDirectory(fullDirectoryPath, targetPath);

        if (File.Exists(targetPath))
        {
            File.Delete(targetPath);
        }

        return Task.CompletedTask;
    }

    public Task DeleteDirectoryAsync(
        string directoryPath,
        string directoryName,
        CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var fullDirectoryPath = Path.GetFullPath(directoryPath);
        var targetPath = Path.GetFullPath(Path.Combine(fullDirectoryPath, directoryName));
        EnsurePathIsWithinDirectory(fullDirectoryPath, targetPath);

        if (Directory.Exists(targetPath))
        {
            Directory.Delete(targetPath, recursive: true);
        }

        return Task.CompletedTask;
    }

    public Task<Stream> OpenReadAsync(
        string directoryPath,
        string fileName,
        CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var fullDirectoryPath = Path.GetFullPath(directoryPath);
        var targetPath = Path.GetFullPath(Path.Combine(fullDirectoryPath, fileName));
        EnsurePathIsWithinDirectory(fullDirectoryPath, targetPath);

        try
        {
            Stream stream = new FileStream(
                targetPath,
                FileMode.Open,
                FileAccess.Read,
                FileShare.Read,
                bufferSize: 81920,
                useAsync: true);

            return Task.FromResult(stream);
        }
        catch (DirectoryNotFoundException)
        {
            throw new FileStorageItemNotFoundException("Wskazany katalog nie istnieje.");
        }
        catch (FileNotFoundException)
        {
            throw new FileStorageItemNotFoundException("Wskazany plik nie istnieje.");
        }
    }

    public Task<bool> FileExistsAsync(
        string directoryPath,
        string fileName,
        CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var fullDirectoryPath = Path.GetFullPath(directoryPath);
        var targetPath = Path.GetFullPath(Path.Combine(fullDirectoryPath, fileName));
        EnsurePathIsWithinDirectory(fullDirectoryPath, targetPath);

        return Task.FromResult(File.Exists(targetPath));
    }

    public Task<IReadOnlyList<StoredFileMetadataDto>> ListFilesAsync(
        string directoryPath,
        CancellationToken cancellationToken = default)
    {
        var fullDirectoryPath = Path.GetFullPath(directoryPath);
        if (!Directory.Exists(fullDirectoryPath))
        {
            return Task.FromResult<IReadOnlyList<StoredFileMetadataDto>>(Array.Empty<StoredFileMetadataDto>());
        }

        var directoryInfo = new DirectoryInfo(fullDirectoryPath);
        var files = new List<StoredFileMetadataDto>();

        foreach (var fileInfo in directoryInfo.EnumerateFiles("*", SearchOption.TopDirectoryOnly))
        {
            cancellationToken.ThrowIfCancellationRequested();
            files.Add(new StoredFileMetadataDto(
                Name: fileInfo.Name,
                SizeBytes: fileInfo.Length,
                LastModifiedUtc: new DateTimeOffset(fileInfo.LastWriteTimeUtc)));
        }

        return Task.FromResult<IReadOnlyList<StoredFileMetadataDto>>(files);
    }

    public Task<IReadOnlyList<StoredDirectoryMetadataDto>> ListDirectoriesAsync(
        string directoryPath,
        CancellationToken cancellationToken = default)
    {
        var fullDirectoryPath = Path.GetFullPath(directoryPath);
        if (!Directory.Exists(fullDirectoryPath))
        {
            return Task.FromResult<IReadOnlyList<StoredDirectoryMetadataDto>>(
                Array.Empty<StoredDirectoryMetadataDto>());
        }

        var directoryInfo = new DirectoryInfo(fullDirectoryPath);
        var directories = new List<StoredDirectoryMetadataDto>();

        foreach (var childDirectory in directoryInfo.EnumerateDirectories("*", SearchOption.TopDirectoryOnly))
        {
            cancellationToken.ThrowIfCancellationRequested();
            directories.Add(new StoredDirectoryMetadataDto(
                Name: childDirectory.Name,
                LastModifiedUtc: new DateTimeOffset(childDirectory.LastWriteTimeUtc)));
        }

        return Task.FromResult<IReadOnlyList<StoredDirectoryMetadataDto>>(directories);
    }

    private static void EnsurePathIsWithinDirectory(string baseDirectoryPath, string targetPath)
    {
        var basePathWithSeparator =
            baseDirectoryPath.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
            + Path.DirectorySeparatorChar;

        if (!targetPath.StartsWith(basePathWithSeparator, StringComparison.Ordinal))
        {
            throw new InvalidOperationException("Resolved file path is outside target directory.");
        }
    }
}
