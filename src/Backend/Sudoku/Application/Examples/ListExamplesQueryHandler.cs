using MediatR;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;

namespace Sudoku.Application.Examples;

public sealed class ListExamplesQueryHandler : IRequestHandler<ListExamplesQuery, ListExamplesQueryResultDto>
{
    private static readonly HashSet<string> SupportedExtensions = new(StringComparer.OrdinalIgnoreCase)
    {
        ".jpg",
        ".jpeg",
        ".png"
    };

    private readonly IFileStorageGateway _fileStorageGateway;
    private readonly ExamplesStorageOptions _storageOptions;

    public ListExamplesQueryHandler(
        IFileStorageGateway fileStorageGateway,
        IOptions<ExamplesStorageOptions> storageOptions)
    {
        _fileStorageGateway = fileStorageGateway;
        _storageOptions = storageOptions.Value;
    }

    public async Task<ListExamplesQueryResultDto> Handle(
        ListExamplesQuery request,
        CancellationToken cancellationToken)
    {
        var uploadsDirectoryPath = ResolveUploadsDirectoryPath();
        var storedFiles = await _fileStorageGateway.ListFilesAsync(uploadsDirectoryPath, cancellationToken);

        var items = storedFiles
            .Where(file => SupportedExtensions.Contains(Path.GetExtension(file.Name)))
            .Select(file => new ListExamplesItemDto(
                Name: file.Name,
                ContentType: ResolveContentType(file.Name),
                SizeBytes: file.SizeBytes,
                StoredAtUtc: file.LastModifiedUtc))
            .OrderByDescending(item => item.StoredAtUtc)
            .ThenBy(item => item.Name, StringComparer.Ordinal)
            .ToArray();

        return new ListExamplesQueryResultDto(
            Items: items,
            TotalCount: items.Length);
    }

    private static string ResolveContentType(string fileName)
    {
        return Path.GetExtension(fileName).ToLowerInvariant() switch
        {
            ".jpg" => "image/jpeg",
            ".jpeg" => "image/jpeg",
            ".png" => "image/png",
            _ => throw new InvalidOperationException($"Unsupported file extension for '{fileName}'.")
        };
    }

    private string ResolveUploadsDirectoryPath()
    {
        var rootPath = Path.GetFullPath(_storageOptions.RootPath);
        return Path.GetFullPath(Path.Combine(rootPath, _storageOptions.UploadsSubdirectory));
    }
}
