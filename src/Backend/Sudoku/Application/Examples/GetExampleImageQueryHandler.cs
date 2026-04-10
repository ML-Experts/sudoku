using MediatR;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;

namespace Sudoku.Application.Examples;

public sealed class GetExampleImageQueryHandler : IRequestHandler<GetExampleImageQuery, GetExampleImageResultDto>
{
    private readonly IFileStorageGateway _fileStorageGateway;
    private readonly ExamplesStorageOptions _storageOptions;

    public GetExampleImageQueryHandler(
        IFileStorageGateway fileStorageGateway,
        IOptions<ExamplesStorageOptions> storageOptions)
    {
        _fileStorageGateway = fileStorageGateway;
        _storageOptions = storageOptions.Value;
    }

    public async Task<GetExampleImageResultDto> Handle(
        GetExampleImageQuery request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.Name))
        {
            throw new InvalidOperationException("GetExampleImageQuery must be validated before handler execution.");
        }

        var uploadsDirectoryPath = ResolveUploadsDirectoryPath();
        await using var imageStream = await _fileStorageGateway.OpenReadAsync(
            uploadsDirectoryPath,
            request.Name,
            cancellationToken);

        await using var buffer = new MemoryStream();
        await imageStream.CopyToAsync(buffer, cancellationToken);

        return new GetExampleImageResultDto(
            MimeType: ResolveMimeType(request.Name),
            Base64: Convert.ToBase64String(buffer.ToArray()));
    }

    private static string ResolveMimeType(string fileName)
    {
        var extension = Path.GetExtension(fileName);
        return extension.ToLowerInvariant() switch
        {
            ".jpg" => "image/jpeg",
            ".jpeg" => "image/jpeg",
            ".png" => "image/png",
            _ => "application/octet-stream"
        };
    }

    private string ResolveUploadsDirectoryPath()
    {
        var rootPath = Path.GetFullPath(_storageOptions.RootPath);
        return Path.GetFullPath(Path.Combine(rootPath, _storageOptions.UploadsSubdirectory));
    }
}
