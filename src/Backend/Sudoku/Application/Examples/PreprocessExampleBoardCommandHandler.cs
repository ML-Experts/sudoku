using MediatR;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Models.Images;

namespace Sudoku.Application.Examples;

public sealed class PreprocessExampleBoardCommandHandler : IRequestHandler<PreprocessExampleBoardCommand, PreprocessBoardResultDto>
{
    private readonly IFileStorageGateway _fileStorageGateway;
    private readonly IMlImageProcessingGateway _mlImageProcessingGateway;
    private readonly ExamplesStorageOptions _storageOptions;

    public PreprocessExampleBoardCommandHandler(
        IFileStorageGateway fileStorageGateway,
        IMlImageProcessingGateway mlImageProcessingGateway,
        IOptions<ExamplesStorageOptions> storageOptions)
    {
        _fileStorageGateway = fileStorageGateway;
        _mlImageProcessingGateway = mlImageProcessingGateway;
        _storageOptions = storageOptions.Value;
    }

    public async Task<PreprocessBoardResultDto> Handle(
        PreprocessExampleBoardCommand request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.Name))
        {
            throw new InvalidOperationException("PreprocessExampleBoardCommand must be validated before handler execution.");
        }

        var uploadsDirectoryPath = ResolveUploadsDirectoryPath();
        await using var imageStream = await _fileStorageGateway.OpenReadAsync(
            uploadsDirectoryPath,
            request.Name,
            cancellationToken);

        await using var buffer = new MemoryStream();
        await imageStream.CopyToAsync(buffer, cancellationToken);

        var sourceImage = new ImageContent(
            MimeType: ResolveMimeType(request.Name),
            Content: buffer.ToArray());

        var processedImage = await _mlImageProcessingGateway.PreprocessBoardAsync(sourceImage, cancellationToken);

        return new PreprocessBoardResultDto(
            MimeType: processedImage.MimeType,
            Base64: Convert.ToBase64String(processedImage.Content));
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
