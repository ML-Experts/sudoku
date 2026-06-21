using MediatR;
using Sudoku.Application.Abstractions;
using Sudoku.Models.Datasets;

namespace Sudoku.Application.Datasets;

public sealed class DeleteDatasetPreparationBoardFileCommandHandler
    : IRequestHandler<DeleteDatasetPreparationBoardFileCommand, DeleteDatasetPreparationBoardFileCommandResultDto>
{
    private const string BoardSourceType = "board";

    private readonly IDatasetPreparationsGateway _datasetPreparationsGateway;
    private readonly IDatasetPreparationArtifactsGateway _datasetPreparationArtifactsGateway;

    public DeleteDatasetPreparationBoardFileCommandHandler(
        IDatasetPreparationsGateway datasetPreparationsGateway,
        IDatasetPreparationArtifactsGateway datasetPreparationArtifactsGateway)
    {
        _datasetPreparationsGateway = datasetPreparationsGateway;
        _datasetPreparationArtifactsGateway = datasetPreparationArtifactsGateway;
    }

    public async Task<DeleteDatasetPreparationBoardFileCommandResultDto> Handle(
        DeleteDatasetPreparationBoardFileCommand request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.PreparationName)
            || string.IsNullOrWhiteSpace(request.SourceName)
            || string.IsNullOrWhiteSpace(request.BoardFolderName))
        {
            throw new InvalidOperationException(
                "DeleteDatasetPreparationBoardFileCommand must be validated before handler execution.");
        }

        var preparationName = request.PreparationName.Trim();
        var sourceName = request.SourceName.Trim();
        var boardFolderName = request.BoardFolderName.Trim();

        var metadata = await _datasetPreparationsGateway.GetByNameAsync(preparationName, cancellationToken);
        if (metadata is null)
        {
            throw new DatasetPreparationNotFoundException(preparationName);
        }

        EnsurePreparationCompleted(metadata);

        var boardSources = await _datasetPreparationArtifactsGateway.GetSourceFolderNamesAsync(
            preparationName,
            BoardSourceType,
            cancellationToken);
        EnsureBoardSourceExists(metadata.PreparationName, sourceName, boardSources);

        var boardFolderNames = await _datasetPreparationArtifactsGateway.GetBoardFileNamesAsync(
            preparationName,
            sourceName,
            cancellationToken);
        EnsureBoardFolderExists(metadata.PreparationName, sourceName, boardFolderName, boardFolderNames);

        var remainingBoardFileNames = BuildRemainingBoardFileNames(boardFolderNames, boardFolderName);

        await PersistManifestThenDeleteBoardAsync(
            preparationName,
            sourceName,
            boardFolderName,
            boardFolderNames,
            remainingBoardFileNames,
            cancellationToken);

        return new DeleteDatasetPreparationBoardFileCommandResultDto(
            PreparationName: metadata.PreparationName,
            SourceName: sourceName,
            BoardFolderName: boardFolderName,
            Deleted: true,
            RemainingItemsCount: remainingBoardFileNames.Count);
    }

    private static void EnsurePreparationCompleted(DatasetPreparationMetadataDto metadata)
    {
        if (!string.Equals(metadata.Status, DatasetPreparationStatus.Completed, StringComparison.OrdinalIgnoreCase))
        {
            throw new DatasetPreparationArtifactsNotReadyException(metadata.PreparationName, metadata.Status);
        }
    }

    private static void EnsureBoardSourceExists(
        string preparationName,
        string sourceName,
        IReadOnlyList<string> boardSources)
    {
        if (!boardSources.Contains(sourceName, StringComparer.Ordinal))
        {
            throw new DatasetPreparationSourceNotFoundException(preparationName, sourceName);
        }
    }

    private static void EnsureBoardFolderExists(
        string preparationName,
        string sourceName,
        string boardFolderName,
        IReadOnlyList<string> boardFolderNames)
    {
        if (!boardFolderNames.Contains(boardFolderName, StringComparer.Ordinal))
        {
            throw new DatasetPreparationBoardFileNotFoundException(preparationName, sourceName, boardFolderName);
        }
    }

    private static IReadOnlyList<string> BuildRemainingBoardFileNames(
        IReadOnlyList<string> boardFolderNames,
        string boardFolderName)
    {
        return boardFolderNames
            .Where(item => !string.Equals(item, boardFolderName, StringComparison.Ordinal))
            .ToArray();
    }

    private async Task PersistManifestThenDeleteBoardAsync(
        string preparationName,
        string sourceName,
        string boardFolderName,
        IReadOnlyList<string> originalBoardFileNames,
        IReadOnlyList<string> remainingBoardFileNames,
        CancellationToken cancellationToken)
    {
        await _datasetPreparationArtifactsGateway.ReplaceBoardFileNamesAsync(
            preparationName,
            sourceName,
            remainingBoardFileNames,
            cancellationToken);

        try
        {
            await _datasetPreparationArtifactsGateway.DeleteBoardDirectoryAsync(
                preparationName,
                sourceName,
                boardFolderName,
                cancellationToken);
        }
        catch (Exception)
        {
            await TryRollbackBoardManifestAsync(
                preparationName,
                sourceName,
                originalBoardFileNames,
                cancellationToken);

            throw;
        }
    }

    private async Task TryRollbackBoardManifestAsync(
        string preparationName,
        string sourceName,
        IReadOnlyList<string> originalBoardFileNames,
        CancellationToken cancellationToken)
    {
        try
        {
            await _datasetPreparationArtifactsGateway.ReplaceBoardFileNamesAsync(
                preparationName,
                sourceName,
                originalBoardFileNames,
                cancellationToken);
        }
        catch
        {
            // Główny błąd usuwania ma zostać propagowany; rollback jest best-effort.
        }
    }
}
