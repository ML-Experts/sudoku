using System.Text.Json;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Datasets;

namespace Sudoku.Infrastructure.Storage;

public sealed class DatasetPreparationArtifactsGateway : IDatasetPreparationArtifactsGateway
{
    private const string BoardSourceType = "board";
    private const string DigitSourceType = "digit";
    private const string ProcessedPreparationsDirectoryName = "preparations";
    private const string FoldersManifestFileName = "folders.json";
    private const string BoardFilesManifestFileName = "file.json";
    private static readonly JsonSerializerOptions JsonSerializerOptions = new(JsonSerializerDefaults.Web);

    private readonly IFileStorageGateway _fileStorageGateway;
    private readonly DatasetsPreparationOptions _datasetsPreparationOptions;

    public DatasetPreparationArtifactsGateway(
        IFileStorageGateway fileStorageGateway,
        IOptions<DatasetsPreparationOptions> datasetsPreparationOptions)
    {
        _fileStorageGateway = fileStorageGateway;
        _datasetsPreparationOptions = datasetsPreparationOptions.Value;
    }

    public async Task<IReadOnlyList<string>> GetSourceFolderNamesAsync(
        string preparationName,
        string sourceType,
        CancellationToken cancellationToken = default)
    {
        var sourceDirectoryPath = await ResolveSourceDirectoryPathAsync(
            preparationName,
            sourceType,
            cancellationToken);
        await using var stream = await _fileStorageGateway.OpenReadAsync(
            sourceDirectoryPath,
            FoldersManifestFileName,
            cancellationToken);

        var items = await JsonSerializer.DeserializeAsync<string[]>(
            stream,
            JsonSerializerOptions,
            cancellationToken);

        if (items is null)
        {
            throw new InvalidDataException(
                $"Manifest folderów preparation '{preparationName}' dla typu '{sourceType}' ma nieprawidłową zawartość.");
        }

        if (items.Any(string.IsNullOrWhiteSpace))
        {
            throw new InvalidDataException(
                $"Manifest folderów preparation '{preparationName}' dla typu '{sourceType}' zawiera puste wpisy.");
        }

        return items;
    }

    public async Task<IReadOnlyList<string>> GetBoardFileNamesAsync(
        string preparationName,
        string sourceName,
        CancellationToken cancellationToken = default)
    {
        var boardSourceDirectoryPath = await ResolveBoardSourceDirectoryPathAsync(
            preparationName,
            sourceName,
            cancellationToken);
        await using var stream = await _fileStorageGateway.OpenReadAsync(
            boardSourceDirectoryPath,
            BoardFilesManifestFileName,
            cancellationToken);

        var items = await JsonSerializer.DeserializeAsync<string[]>(
            stream,
            JsonSerializerOptions,
            cancellationToken);

        if (items is null)
        {
            throw new InvalidDataException(
                $"Manifest plików plansz preparation '{preparationName}' dla źródła '{sourceName}' ma nieprawidłową zawartość.");
        }

        if (items.Any(string.IsNullOrWhiteSpace))
        {
            throw new InvalidDataException(
                $"Manifest plików plansz preparation '{preparationName}' dla źródła '{sourceName}' zawiera puste wpisy.");
        }

        return items;
    }

    public Task<Stream> OpenBoardArtifactReadAsync(
        string preparationName,
        string sourceName,
        string boardFolderName,
        string artifactFileName,
        CancellationToken cancellationToken = default)
    {
        return OpenBoardArtifactReadInternalAsync(
            preparationName,
            sourceName,
            boardFolderName,
            artifactFileName,
            cancellationToken);
    }

    public async Task ReplaceBoardFileNamesAsync(
        string preparationName,
        string sourceName,
        IReadOnlyList<string> boardFileNames,
        CancellationToken cancellationToken = default)
    {
        var boardSourceDirectoryPath = await ResolveBoardSourceDirectoryPathAsync(
            preparationName,
            sourceName,
            cancellationToken);
        await using var payloadStream = new MemoryStream(
            JsonSerializer.SerializeToUtf8Bytes(boardFileNames, JsonSerializerOptions));

        await _fileStorageGateway.ReplaceAsync(
            boardSourceDirectoryPath,
            BoardFilesManifestFileName,
            payloadStream,
            cancellationToken);
    }

    public Task DeleteBoardDirectoryAsync(
        string preparationName,
        string sourceName,
        string boardFolderName,
        CancellationToken cancellationToken = default)
    {
        return DeleteBoardDirectoryInternalAsync(
            preparationName,
            sourceName,
            boardFolderName,
            cancellationToken);
    }

    private async Task<Stream> OpenBoardArtifactReadInternalAsync(
        string preparationName,
        string sourceName,
        string boardFolderName,
        string artifactFileName,
        CancellationToken cancellationToken)
    {
        var boardArtifactDirectoryPath = await ResolveBoardArtifactDirectoryPathAsync(
            preparationName,
            sourceName,
            boardFolderName,
            cancellationToken);

        return await _fileStorageGateway.OpenReadAsync(
            boardArtifactDirectoryPath,
            artifactFileName,
            cancellationToken);
    }

    private async Task DeleteBoardDirectoryInternalAsync(
        string preparationName,
        string sourceName,
        string boardFolderName,
        CancellationToken cancellationToken)
    {
        var boardSourceDirectoryPath = await ResolveBoardSourceDirectoryPathAsync(
            preparationName,
            sourceName,
            cancellationToken);

        await _fileStorageGateway.DeleteDirectoryAsync(
            boardSourceDirectoryPath,
            boardFolderName,
            cancellationToken);
    }

    private async Task<string> ResolveSourceDirectoryPathAsync(
        string preparationName,
        string sourceType,
        CancellationToken cancellationToken)
    {
        var sourceDirectoryName = MapSourceTypeDirectoryName(sourceType);

        foreach (var preparationArtifactsRootPath in GetPreparationArtifactsRootCandidates(preparationName))
        {
            var sourceDirectoryPath = Path.Combine(preparationArtifactsRootPath, sourceDirectoryName);
            if (await _fileStorageGateway.FileExistsAsync(
                    sourceDirectoryPath,
                    FoldersManifestFileName,
                    cancellationToken))
            {
                return sourceDirectoryPath;
            }
        }

        return Path.Combine(BuildPreparationMetadataRootPath(preparationName), sourceDirectoryName);
    }

    private async Task<string> ResolveBoardSourceDirectoryPathAsync(
        string preparationName,
        string sourceName,
        CancellationToken cancellationToken)
    {
        foreach (var preparationArtifactsRootPath in GetPreparationArtifactsRootCandidates(preparationName))
        {
            var boardSourceDirectoryPath = Path.Combine(
                preparationArtifactsRootPath,
                BoardSourceType,
                sourceName);
            if (await _fileStorageGateway.FileExistsAsync(
                    boardSourceDirectoryPath,
                    BoardFilesManifestFileName,
                    cancellationToken))
            {
                return boardSourceDirectoryPath;
            }
        }

        return Path.Combine(
            BuildPreparationMetadataRootPath(preparationName),
            BoardSourceType,
            sourceName);
    }

    private async Task<string> ResolveBoardArtifactDirectoryPathAsync(
        string preparationName,
        string sourceName,
        string boardFolderName,
        CancellationToken cancellationToken)
    {
        var boardSourceDirectoryPath = await ResolveBoardSourceDirectoryPathAsync(
            preparationName,
            sourceName,
            cancellationToken);

        return Path.Combine(
            boardSourceDirectoryPath,
            boardFolderName);
    }

    private IEnumerable<string> GetPreparationArtifactsRootCandidates(string preparationName)
    {
        var seenPaths = new HashSet<string>(StringComparer.Ordinal);
        var candidatePaths =
            new[]
            {
                BuildPreparationMetadataRootPath(preparationName),
                BuildProcessedPreparationArtifactsRootPath(preparationName)
            };

        foreach (var candidatePath in candidatePaths.Select(Path.GetFullPath))
        {
            if (seenPaths.Add(candidatePath))
            {
                yield return candidatePath;
            }
        }
    }

    private string BuildPreparationMetadataRootPath(string preparationName)
    {
        return Path.Combine(_datasetsPreparationOptions.PreparationsDirectoryPath, preparationName);
    }

    private string BuildProcessedPreparationArtifactsRootPath(string preparationName)
    {
        return Path.Combine(
            _datasetsPreparationOptions.ProcessedDatasetsDirectoryPath,
            ProcessedPreparationsDirectoryName,
            preparationName);
    }

    private static string MapSourceTypeDirectoryName(string sourceType)
    {
        if (string.Equals(sourceType, BoardSourceType, StringComparison.OrdinalIgnoreCase))
        {
            return BoardSourceType;
        }

        if (string.Equals(sourceType, DigitSourceType, StringComparison.OrdinalIgnoreCase))
        {
            return DigitSourceType;
        }

        throw new InvalidOperationException($"Nieobsługiwany typ preparation artifacts: '{sourceType}'.");
    }
}
