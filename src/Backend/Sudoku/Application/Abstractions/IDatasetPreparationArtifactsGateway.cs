namespace Sudoku.Application.Abstractions;

public interface IDatasetPreparationArtifactsGateway
{
    Task<IReadOnlyList<string>> GetSourceFolderNamesAsync(
        string preparationName,
        string sourceType,
        CancellationToken cancellationToken = default);

    Task<IReadOnlyList<string>> GetBoardFileNamesAsync(
        string preparationName,
        string sourceName,
        CancellationToken cancellationToken = default);

    Task<Stream> OpenBoardArtifactReadAsync(
        string preparationName,
        string sourceName,
        string boardFolderName,
        string artifactFileName,
        CancellationToken cancellationToken = default);

    Task ReplaceBoardFileNamesAsync(
        string preparationName,
        string sourceName,
        IReadOnlyList<string> boardFileNames,
        CancellationToken cancellationToken = default);

    Task DeleteBoardDirectoryAsync(
        string preparationName,
        string sourceName,
        string boardFolderName,
        CancellationToken cancellationToken = default);
}
