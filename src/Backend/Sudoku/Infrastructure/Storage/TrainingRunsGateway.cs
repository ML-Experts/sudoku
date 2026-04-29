using System.Text.Json;
using System.Text;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Storage;
using Sudoku.Application.Trainings;

namespace Sudoku.Infrastructure.Storage;

public sealed class TrainingRunsGateway : ITrainingRunsGateway
{
    private static readonly JsonSerializerOptions JsonSerializerOptions = new(JsonSerializerDefaults.Web);

    private readonly IFileStorageGateway _fileStorageGateway;
    private readonly TrainingsStorageOptions _trainingsStorageOptions;

    public TrainingRunsGateway(
        IFileStorageGateway fileStorageGateway,
        IOptions<TrainingsStorageOptions> trainingsStorageOptions)
    {
        _fileStorageGateway = fileStorageGateway;
        _trainingsStorageOptions = trainingsStorageOptions.Value;
    }

    public async Task<IReadOnlyList<TrainingRunMetadataDto>> ListAsync(
        CancellationToken cancellationToken = default)
    {
        var files = await _fileStorageGateway.ListFilesAsync(
            _trainingsStorageOptions.MetadataDirectoryPath,
            cancellationToken);

        var metadataFiles = files
            .Where(file => file.Name.EndsWith(".json", StringComparison.OrdinalIgnoreCase))
            .OrderBy(file => file.Name, StringComparer.Ordinal)
            .ToArray();

        var results = new List<TrainingRunMetadataDto>(metadataFiles.Length);
        foreach (var metadataFile in metadataFiles)
        {
            cancellationToken.ThrowIfCancellationRequested();

            await using var stream = await _fileStorageGateway.OpenReadAsync(
                _trainingsStorageOptions.MetadataDirectoryPath,
                metadataFile.Name,
                cancellationToken);

            var metadata = await JsonSerializer.DeserializeAsync<TrainingRunMetadataDto>(
                stream,
                JsonSerializerOptions,
                cancellationToken);

            if (metadata is null)
            {
                throw new InvalidDataException(
                    $"Plik metadanych runu {metadataFile.Name} ma nieprawidłową zawartość.");
            }

            results.Add(metadata);
        }

        return results;
    }

    public async Task<TrainingRunMetadataDto?> GetByRunNameAsync(
        string runName,
        CancellationToken cancellationToken = default)
    {
        try
        {
            await using var stream = await _fileStorageGateway.OpenReadAsync(
                _trainingsStorageOptions.MetadataDirectoryPath,
                BuildMetadataFileName(runName),
                cancellationToken);

            var metadata = await JsonSerializer.DeserializeAsync<TrainingRunMetadataDto>(
                stream,
                JsonSerializerOptions,
                cancellationToken);

            return metadata ?? throw new InvalidDataException(
                $"Plik metadanych runu {runName} ma nieprawidłową zawartość.");
        }
        catch (FileStorageItemNotFoundException)
        {
            return null;
        }
    }

    public async Task<bool> TryCreateAsync(
        TrainingRunMetadataDto metadata,
        CancellationToken cancellationToken = default)
    {
        try
        {
            await using var content = CreateMetadataStream(metadata);
            await _fileStorageGateway.SaveAsync(
                _trainingsStorageOptions.MetadataDirectoryPath,
                BuildMetadataFileName(metadata.RunName),
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
        TrainingRunMetadataDto metadata,
        CancellationToken cancellationToken = default)
    {
        await using var content = CreateMetadataStream(metadata);
        await _fileStorageGateway.ReplaceAsync(
            _trainingsStorageOptions.MetadataDirectoryPath,
            BuildMetadataFileName(metadata.RunName),
            content,
            cancellationToken);
    }

    public Task DeleteAsync(
        string runName,
        CancellationToken cancellationToken = default)
    {
        return _fileStorageGateway.DeleteAsync(
            _trainingsStorageOptions.MetadataDirectoryPath,
            BuildMetadataFileName(runName),
            cancellationToken);
    }

    private static MemoryStream CreateMetadataStream(TrainingRunMetadataDto metadata)
    {
        var payload = JsonSerializer.Serialize(metadata, JsonSerializerOptions);
        return new MemoryStream(Encoding.UTF8.GetBytes(payload));
    }

    private static string BuildMetadataFileName(string runName)
    {
        return $"{runName}.json";
    }
}
