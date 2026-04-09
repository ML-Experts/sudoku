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
