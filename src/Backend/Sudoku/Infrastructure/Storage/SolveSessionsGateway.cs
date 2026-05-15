using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Storage;
using Sudoku.Application.SudokuSolve;

namespace Sudoku.Infrastructure.Storage;

public sealed class SolveSessionsGateway : ISolveSessionsGateway
{
    private static readonly JsonSerializerOptions JsonSerializerOptions = new(JsonSerializerDefaults.Web);

    private readonly IFileStorageGateway _fileStorageGateway;
    private readonly SudokuSolveSessionsStorageOptions _options;

    public SolveSessionsGateway(
        IFileStorageGateway fileStorageGateway,
        IOptions<SudokuSolveSessionsStorageOptions> options)
    {
        _fileStorageGateway = fileStorageGateway;
        _options = options.Value;
    }

    public async Task<IReadOnlyList<SolveSessionMetadataDto>> ListAsync(
        CancellationToken cancellationToken = default)
    {
        var files = await _fileStorageGateway.ListFilesAsync(
            _options.MetadataDirectoryPath,
            cancellationToken);

        var metadataFiles = files
            .Where(file => file.Name.EndsWith(".json", StringComparison.OrdinalIgnoreCase))
            .OrderBy(file => file.Name, StringComparer.Ordinal)
            .ToArray();

        var results = new List<SolveSessionMetadataDto>(metadataFiles.Length);
        foreach (var metadataFile in metadataFiles)
        {
            cancellationToken.ThrowIfCancellationRequested();

            await using var stream = await _fileStorageGateway.OpenReadAsync(
                _options.MetadataDirectoryPath,
                metadataFile.Name,
                cancellationToken);

            var metadata = await JsonSerializer.DeserializeAsync<SolveSessionMetadataDto>(
                stream,
                JsonSerializerOptions,
                cancellationToken);

            if (metadata is null)
            {
                throw new InvalidDataException(
                    $"Plik metadanych sesji solve {metadataFile.Name} ma nieprawidłową zawartość.");
            }

            results.Add(metadata);
        }

        return results;
    }

    public async Task<SolveSessionMetadataDto?> GetBySolveSessionIdAsync(
        string solveSessionId,
        CancellationToken cancellationToken = default)
    {
        try
        {
            await using var stream = await _fileStorageGateway.OpenReadAsync(
                _options.MetadataDirectoryPath,
                BuildMetadataFileName(solveSessionId),
                cancellationToken);

            var metadata = await JsonSerializer.DeserializeAsync<SolveSessionMetadataDto>(
                stream,
                JsonSerializerOptions,
                cancellationToken);

            return metadata ?? throw new InvalidDataException(
                $"Plik metadanych sesji solve {solveSessionId} ma nieprawidłową zawartość.");
        }
        catch (FileStorageItemNotFoundException)
        {
            return null;
        }
    }

    public async Task<bool> TryCreateAsync(
        SolveSessionMetadataDto metadata,
        CancellationToken cancellationToken = default)
    {
        try
        {
            await using var content = CreateMetadataStream(metadata);
            await _fileStorageGateway.SaveAsync(
                _options.MetadataDirectoryPath,
                BuildMetadataFileName(metadata.SolveSessionId),
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
        SolveSessionMetadataDto metadata,
        CancellationToken cancellationToken = default)
    {
        await using var content = CreateMetadataStream(metadata);
        await _fileStorageGateway.ReplaceAsync(
            _options.MetadataDirectoryPath,
            BuildMetadataFileName(metadata.SolveSessionId),
            content,
            cancellationToken);
    }

    public Task DeleteAsync(
        string solveSessionId,
        CancellationToken cancellationToken = default)
    {
        return _fileStorageGateway.DeleteAsync(
            _options.MetadataDirectoryPath,
            BuildMetadataFileName(solveSessionId),
            cancellationToken);
    }

    private static MemoryStream CreateMetadataStream(SolveSessionMetadataDto metadata)
    {
        var payload = JsonSerializer.Serialize(metadata, JsonSerializerOptions);
        return new MemoryStream(Encoding.UTF8.GetBytes(payload));
    }

    private static string BuildMetadataFileName(string solveSessionId)
    {
        return $"{solveSessionId}.json";
    }
}
