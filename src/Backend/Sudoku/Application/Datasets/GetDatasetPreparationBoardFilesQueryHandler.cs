using MediatR;
using Sudoku.Application.Abstractions;
using Sudoku.Models.Datasets;

namespace Sudoku.Application.Datasets;

public sealed class GetDatasetPreparationBoardFilesQueryHandler
    : IRequestHandler<GetDatasetPreparationBoardFilesQuery, GetDatasetPreparationBoardFilesQueryResultDto>
{
    private readonly IDatasetPreparationsGateway _datasetPreparationsGateway;
    private readonly IDatasetPreparationArtifactsGateway _datasetPreparationArtifactsGateway;

    public GetDatasetPreparationBoardFilesQueryHandler(
        IDatasetPreparationsGateway datasetPreparationsGateway,
        IDatasetPreparationArtifactsGateway datasetPreparationArtifactsGateway)
    {
        _datasetPreparationsGateway = datasetPreparationsGateway;
        _datasetPreparationArtifactsGateway = datasetPreparationArtifactsGateway;
    }

    public async Task<GetDatasetPreparationBoardFilesQueryResultDto> Handle(
        GetDatasetPreparationBoardFilesQuery request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.PreparationName)
            || string.IsNullOrWhiteSpace(request.SourceName)
            || !request.Page.HasValue
            || !request.PageSize.HasValue
            || request.Page.Value < 1
            || request.PageSize.Value < 1)
        {
            throw new InvalidOperationException(
                "GetDatasetPreparationBoardFilesQuery must be validated before handler execution.");
        }

        var preparationName = request.PreparationName.Trim();
        var sourceName = request.SourceName.Trim();
        var page = request.Page.Value;
        var pageSize = request.PageSize.Value;

        var metadata = await _datasetPreparationsGateway.GetByNameAsync(preparationName, cancellationToken);
        if (metadata is null)
        {
            throw new DatasetPreparationNotFoundException(preparationName);
        }

        EnsurePreparationCompleted(metadata);

        var boardSources = await _datasetPreparationArtifactsGateway.GetSourceFolderNamesAsync(
            preparationName,
            "board",
            cancellationToken);
        EnsureBoardSourceExists(metadata.PreparationName, sourceName, boardSources);

        var boardFolderNames = await _datasetPreparationArtifactsGateway.GetBoardFileNamesAsync(
            preparationName,
            sourceName,
            cancellationToken);

        var pageItems = Paginate(boardFolderNames, page, pageSize)
            .Select(boardFolderName => new DatasetPreparationBoardFileListItemDto(boardFolderName))
            .ToArray();

        return new GetDatasetPreparationBoardFilesQueryResultDto(
            PreparationName: metadata.PreparationName,
            SourceName: sourceName,
            Items: pageItems,
            Page: page,
            PageSize: pageSize,
            TotalCount: boardFolderNames.Count);
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

    private static IReadOnlyList<string> Paginate(IReadOnlyList<string> items, int page, int pageSize)
    {
        var skip = (page - 1) * pageSize;
        if (skip >= items.Count)
        {
            return [];
        }

        return items
            .Skip(skip)
            .Take(pageSize)
            .ToArray();
    }
}
