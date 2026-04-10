using MediatR;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;

namespace Sudoku.Application.Examples;

public sealed class UploadExampleCommandHandler : IRequestHandler<UploadExampleCommand, UploadExampleCommandResultDto>
{
    private readonly IFileStorageGateway _fileStorageGateway;
    private readonly ExamplesStorageOptions _storageOptions;
    private readonly TimeProvider _timeProvider;

    public UploadExampleCommandHandler(
        IFileStorageGateway fileStorageGateway,
        IOptions<ExamplesStorageOptions> storageOptions,
        TimeProvider timeProvider)
    {
        _fileStorageGateway = fileStorageGateway;
        _storageOptions = storageOptions.Value;
        _timeProvider = timeProvider;
    }

    public async Task<UploadExampleCommandResultDto> Handle(
        UploadExampleCommand request,
        CancellationToken cancellationToken)
    {
        if (request.FileStream is null || request.SizeBytes is null || string.IsNullOrWhiteSpace(request.ContentType))
        {
            throw new InvalidOperationException("UploadExampleCommand must be validated before handler execution.");
        }

        var storedAtUtc = _timeProvider.GetUtcNow();
        var fileExtension = ResolveFileExtension(request.ContentType);
        var canonicalName = CreateCanonicalName(storedAtUtc, fileExtension);
        var uploadsDirectoryPath = ResolveUploadsDirectoryPath();

        await _fileStorageGateway.SaveAsync(
            uploadsDirectoryPath,
            canonicalName,
            request.FileStream,
            cancellationToken);

        return new UploadExampleCommandResultDto(
            Name: canonicalName,
            ContentType: request.ContentType,
            SizeBytes: request.SizeBytes.Value,
            StoredAtUtc: storedAtUtc);
    }

    private static string ResolveFileExtension(string contentType)
    {
        return contentType.ToLowerInvariant() switch
        {
            "image/jpeg" => "jpg",
            "image/jpg" => "jpg",
            "image/png" => "png",
            _ => throw new InvalidOperationException($"Unsupported content type '{contentType}'.")
        };
    }

    private static string CreateCanonicalName(DateTimeOffset storedAtUtc, string extension)
    {
        var timestamp = storedAtUtc.ToString("yyyyMMdd-HHmmss");
        var suffix = Guid.NewGuid().ToString("N")[..6];
        return $"sudoku-{timestamp}-{suffix}.{extension}";
    }

    private string ResolveUploadsDirectoryPath()
    {
        var rootPath = Path.GetFullPath(_storageOptions.RootPath);
        return Path.GetFullPath(Path.Combine(rootPath, _storageOptions.UploadsSubdirectory));
    }
}
