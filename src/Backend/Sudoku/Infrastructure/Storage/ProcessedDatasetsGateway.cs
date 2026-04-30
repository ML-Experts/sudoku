using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Datasets;
using Sudoku.Application.Storage;

namespace Sudoku.Infrastructure.Storage;

public sealed class ProcessedDatasetsGateway : IProcessedDatasetsGateway
{
    private const string MetadataSuffix = ".metadata.json";
    private static readonly JsonSerializerOptions JsonSerializerOptions = new(JsonSerializerDefaults.Web);

    private readonly IFileStorageGateway _fileStorageGateway;
    private readonly DatasetsPreparationOptions _datasetsPreparationOptions;

    public ProcessedDatasetsGateway(
        IFileStorageGateway fileStorageGateway,
        IOptions<DatasetsPreparationOptions> datasetsPreparationOptions)
    {
        _fileStorageGateway = fileStorageGateway;
        _datasetsPreparationOptions = datasetsPreparationOptions.Value;
    }

    public async Task<bool> IsProcessedDatasetNameAvailableAsync(
        string datasetName,
        CancellationToken cancellationToken = default)
    {
        var targetNpzName = $"{datasetName}.npz";
        var targetMetadataName = BuildMetadataFileName(datasetName);

        var files = await _fileStorageGateway.ListFilesAsync(
            _datasetsPreparationOptions.ProcessedDatasetsDirectoryPath,
            cancellationToken);

        return files.All(file =>
            !string.Equals(file.Name, targetNpzName, StringComparison.OrdinalIgnoreCase)
            && !string.Equals(file.Name, targetMetadataName, StringComparison.OrdinalIgnoreCase));
    }

    public async Task PromotePreparedArtifactAsync(
        string datasetName,
        string targetFileName,
        CancellationToken cancellationToken = default)
    {
        var temporaryArtifactName = $"{datasetName}.npz";

        await using var artifactContent = await _fileStorageGateway.OpenReadAsync(
            _datasetsPreparationOptions.TemporaryArtifactsDirectoryPath,
            temporaryArtifactName,
            cancellationToken);

        await _fileStorageGateway.SaveAsync(
            _datasetsPreparationOptions.ProcessedDatasetsDirectoryPath,
            targetFileName,
            artifactContent,
            cancellationToken);
    }

    public async Task SaveMetadataAsync(
        ProcessedDatasetMetadataDto metadata,
        CancellationToken cancellationToken = default)
    {
        var metadataPayload = JsonSerializer.Serialize(metadata, JsonSerializerOptions);
        await using var content = new MemoryStream(Encoding.UTF8.GetBytes(metadataPayload));

        await _fileStorageGateway.SaveAsync(
            _datasetsPreparationOptions.ProcessedDatasetsDirectoryPath,
            BuildMetadataFileName(metadata.Name),
            content,
            cancellationToken);
    }

    public async Task<IReadOnlyList<ProcessedDatasetMetadataDto>> ListAsync(CancellationToken cancellationToken = default)
    {
        var files = await _fileStorageGateway.ListFilesAsync(
            _datasetsPreparationOptions.ProcessedDatasetsDirectoryPath,
            cancellationToken);

        var metadataFiles = files
            .Where(file => file.Name.EndsWith(MetadataSuffix, StringComparison.OrdinalIgnoreCase))
            .OrderBy(file => file.Name, StringComparer.Ordinal)
            .ToArray();

        var results = new List<ProcessedDatasetMetadataDto>(metadataFiles.Length);
        foreach (var metadataFile in metadataFiles)
        {
            cancellationToken.ThrowIfCancellationRequested();

            await using var stream = await _fileStorageGateway.OpenReadAsync(
                _datasetsPreparationOptions.ProcessedDatasetsDirectoryPath,
                metadataFile.Name,
                cancellationToken);

            var metadata = await JsonSerializer.DeserializeAsync<ProcessedDatasetMetadataDto>(
                stream,
                JsonSerializerOptions,
                cancellationToken);

            if (metadata is null)
            {
                throw new InvalidDataException($"Plik metadanych {metadataFile.Name} ma nieprawidłową zawartość.");
            }

            results.Add(metadata);
        }

        return results;
    }

    public async Task<ProcessedDatasetMetadataDto?> GetByNameAsync(
        string datasetName,
        CancellationToken cancellationToken = default)
    {
        var metadataFileName = BuildMetadataFileName(datasetName);
        var files = await _fileStorageGateway.ListFilesAsync(
            _datasetsPreparationOptions.ProcessedDatasetsDirectoryPath,
            cancellationToken);

        if (!files.Any(file => string.Equals(file.Name, metadataFileName, StringComparison.OrdinalIgnoreCase)))
        {
            return null;
        }

        await using var stream = await _fileStorageGateway.OpenReadAsync(
            _datasetsPreparationOptions.ProcessedDatasetsDirectoryPath,
            metadataFileName,
            cancellationToken);

        var metadata = await JsonSerializer.DeserializeAsync<ProcessedDatasetMetadataDto>(
            stream,
            JsonSerializerOptions,
            cancellationToken);

        if (metadata is null)
        {
            throw new InvalidDataException($"Plik metadanych {metadataFileName} ma nieprawidłową zawartość.");
        }

        if (!string.Equals(metadata.Name, datasetName, StringComparison.Ordinal))
        {
            throw new InvalidDataException(
                $"Nazwa datasetu {metadata.Name} w metadanych nie odpowiada żądanemu datasetowi {datasetName}.");
        }

        var fileName = string.IsNullOrWhiteSpace(metadata.FileName)
            ? $"{datasetName}.npz"
            : metadata.FileName;
        if (!files.Any(file => string.Equals(file.Name, fileName, StringComparison.OrdinalIgnoreCase)))
        {
            return null;
        }

        return metadata;
    }

    private static string BuildMetadataFileName(string datasetName)
    {
        return $"{datasetName}{MetadataSuffix}";
    }
}
