using MediatR;
using Sudoku.Application.Abstractions;
using Sudoku.Models.Datasets;

namespace Sudoku.Application.Datasets;

public sealed class GetDatasetPreparationBoardImageQueryHandler
    : IRequestHandler<GetDatasetPreparationBoardImageQuery, GetDatasetPreparationBoardImageQueryResultDto>
{
    private const string BoardSourceType = "board";
    private const string BoardImageMimeType = "image/png";

    private readonly IDatasetPreparationsGateway _datasetPreparationsGateway;
    private readonly IDatasetPreparationArtifactsGateway _datasetPreparationArtifactsGateway;

    public GetDatasetPreparationBoardImageQueryHandler(
        IDatasetPreparationsGateway datasetPreparationsGateway,
        IDatasetPreparationArtifactsGateway datasetPreparationArtifactsGateway)
    {
        _datasetPreparationsGateway = datasetPreparationsGateway;
        _datasetPreparationArtifactsGateway = datasetPreparationArtifactsGateway;
    }

    public async Task<GetDatasetPreparationBoardImageQueryResultDto> Handle(
        GetDatasetPreparationBoardImageQuery request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.PreparationName)
            || string.IsNullOrWhiteSpace(request.SourceName)
            || string.IsNullOrWhiteSpace(request.BoardFolderName))
        {
            throw new InvalidOperationException(
                "GetDatasetPreparationBoardImageQuery must be validated before handler execution.");
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

        var base64 = await ReadArtifactAsBase64Async(
            preparationName,
            sourceName,
            boardFolderName,
            cancellationToken);

        return new GetDatasetPreparationBoardImageQueryResultDto(
            MimeType: BoardImageMimeType,
            Base64: base64);
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

    private async Task<string> ReadArtifactAsBase64Async(
        string preparationName,
        string sourceName,
        string boardFolderName,
        CancellationToken cancellationToken)
    {
        await using var artifactStream = await _datasetPreparationArtifactsGateway.OpenBoardArtifactReadAsync(
            preparationName,
            sourceName,
            boardFolderName,
            DatasetPreparationBoardArtifactNames.CorrectedBoardFileName,
            cancellationToken);
        await using var buffer = new MemoryStream();
        await artifactStream.CopyToAsync(buffer, cancellationToken);

        return Convert.ToBase64String(buffer.ToArray());
    }
}
