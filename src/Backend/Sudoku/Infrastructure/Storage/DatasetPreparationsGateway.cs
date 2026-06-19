using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Datasets;
using Sudoku.Application.Storage;

namespace Sudoku.Infrastructure.Storage;

public sealed class DatasetPreparationsGateway : IDatasetPreparationsGateway
{
    private const string MetadataFileName = "preparation.metadata.json";
    private static readonly JsonSerializerOptions JsonSerializerOptions = new(JsonSerializerDefaults.Web);

    private readonly IFileStorageGateway _fileStorageGateway;
    private readonly DatasetsPreparationOptions _datasetsPreparationOptions;

    public DatasetPreparationsGateway(
        IFileStorageGateway fileStorageGateway,
        IOptions<DatasetsPreparationOptions> datasetsPreparationOptions)
    {
        _fileStorageGateway = fileStorageGateway;
        _datasetsPreparationOptions = datasetsPreparationOptions.Value;
    }

    public async Task<IReadOnlyList<DatasetPreparationMetadataDto>> ListAsync(
        CancellationToken cancellationToken = default)
    {
        var directories = await _fileStorageGateway.ListDirectoriesAsync(
            _datasetsPreparationOptions.PreparationsDirectoryPath,
            cancellationToken);

        var results = new List<DatasetPreparationMetadataDto>(directories.Count);
        foreach (var directory in directories.OrderBy(item => item.Name, StringComparer.Ordinal))
        {
            cancellationToken.ThrowIfCancellationRequested();

            var metadata = await GetByNameAsync(directory.Name, cancellationToken);
            if (metadata is not null)
            {
                results.Add(metadata);
            }
        }

        return results;
    }

    public async Task<DatasetPreparationMetadataDto?> GetByNameAsync(
        string preparationName,
        CancellationToken cancellationToken = default)
    {
        try
        {
            await using var stream = await _fileStorageGateway.OpenReadAsync(
                BuildPreparationDirectoryPath(preparationName),
                MetadataFileName,
                cancellationToken);

            var metadata = await JsonSerializer.DeserializeAsync<DatasetPreparationMetadataDto>(
                stream,
                JsonSerializerOptions,
                cancellationToken);

            if (metadata is null)
            {
                throw new InvalidDataException(
                    $"Plik metadanych przygotowania {preparationName} ma nieprawidłową zawartość.");
            }

            if (!string.Equals(metadata.PreparationName, preparationName, StringComparison.Ordinal))
            {
                throw new InvalidDataException(
                    $"Nazwa przygotowania {metadata.PreparationName} w metadanych nie odpowiada żądanemu przygotowaniu {preparationName}.");
            }

            return metadata;
        }
        catch (FileStorageItemNotFoundException)
        {
            return null;
        }
    }

    public async Task<bool> TryCreateAsync(
        DatasetPreparationMetadataDto metadata,
        CancellationToken cancellationToken = default)
    {
        try
        {
            await using var content = CreateMetadataStream(metadata);
            await _fileStorageGateway.SaveAsync(
                BuildPreparationDirectoryPath(metadata.PreparationName),
                MetadataFileName,
                content,
                cancellationToken);

            return true;
        }
        catch (FileStorageConflictException)
        {
            return false;
        }
    }

    public async Task UpdateAsync(
        DatasetPreparationMetadataDto metadata,
        CancellationToken cancellationToken = default)
    {
        await using var content = CreateMetadataStream(metadata);
        await _fileStorageGateway.ReplaceAsync(
            BuildPreparationDirectoryPath(metadata.PreparationName),
            MetadataFileName,
            content,
            cancellationToken);
    }

    public Task CleanupGeneratedContentAsync(
        string preparationName,
        CancellationToken cancellationToken = default)
    {
        return _fileStorageGateway.DeleteDirectoryAsync(
            _datasetsPreparationOptions.PreparationsDirectoryPath,
            preparationName,
            cancellationToken);
    }

    private string BuildPreparationDirectoryPath(string preparationName)
    {
        return Path.Combine(_datasetsPreparationOptions.PreparationsDirectoryPath, preparationName);
    }

    private static MemoryStream CreateMetadataStream(DatasetPreparationMetadataDto metadata)
    {
        var payload = JsonSerializer.Serialize(metadata, JsonSerializerOptions);
        return new MemoryStream(Encoding.UTF8.GetBytes(payload));
    }
}
