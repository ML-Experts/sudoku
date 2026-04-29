using System.Text.Json;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
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
}
