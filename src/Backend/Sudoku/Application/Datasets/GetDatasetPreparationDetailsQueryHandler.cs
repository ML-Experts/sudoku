using MediatR;
using Sudoku.Application.Abstractions;

namespace Sudoku.Application.Datasets;

public sealed class GetDatasetPreparationDetailsQueryHandler
    : IRequestHandler<GetDatasetPreparationDetailsQuery, GetDatasetPreparationDetailsQueryResultDto>
{
    private readonly IDatasetPreparationsGateway _datasetPreparationsGateway;

    public GetDatasetPreparationDetailsQueryHandler(IDatasetPreparationsGateway datasetPreparationsGateway)
    {
        _datasetPreparationsGateway = datasetPreparationsGateway;
    }

    public async Task<GetDatasetPreparationDetailsQueryResultDto> Handle(
        GetDatasetPreparationDetailsQuery request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.PreparationName))
        {
            throw new InvalidOperationException(
                "GetDatasetPreparationDetailsQuery must be validated before handler execution.");
        }

        var preparationName = request.PreparationName.Trim();
        var metadata = await _datasetPreparationsGateway.GetByNameAsync(preparationName, cancellationToken);
        if (metadata is null)
        {
            throw new DatasetPreparationNotFoundException(preparationName);
        }

        return MapToResultDto(metadata);
    }

    private static GetDatasetPreparationDetailsQueryResultDto MapToResultDto(
        DatasetPreparationMetadataDto metadata)
    {
        if (metadata.Sources is null)
        {
            throw new InvalidDataException(
                $"Metadane przygotowania {metadata.PreparationName} nie zawierają listy źródeł.");
        }

        return new GetDatasetPreparationDetailsQueryResultDto(
            PreparationName: metadata.PreparationName,
            CreatedAtUtc: metadata.CreatedAtUtc,
            Status: metadata.Status,
            Sources: MapSourceReports(metadata.Sources, metadata.SourceReports),
            Warnings: NormalizeWarnings(metadata.Warnings));
    }

    private static IReadOnlyList<DatasetPreparationSourceReportDto> MapSourceReports(
        IReadOnlyList<CreateDatasetPreparationSourceDto> sources,
        IReadOnlyList<DatasetPreparationSourceReportDto>? sourceReports)
    {
        var reportsByKey = (sourceReports ?? Array.Empty<DatasetPreparationSourceReportDto>())
            .GroupBy(CreateKey, StringComparer.OrdinalIgnoreCase)
            .ToDictionary(group => group.Key, group => group.First(), StringComparer.OrdinalIgnoreCase);

        return sources
            .Select(source =>
            {
                var sourceKey = CreateKey(source.Name, source.Type);
                if (!reportsByKey.TryGetValue(sourceKey, out var report))
                {
                    return new DatasetPreparationSourceReportDto(
                        Name: source.Name,
                        Type: source.Type,
                        PreparedItemsCount: 0,
                        RejectedItemsCount: 0,
                        EmptyCellCount: 0);
                }

                return new DatasetPreparationSourceReportDto(
                    Name: source.Name,
                    Type: source.Type,
                    PreparedItemsCount: report.PreparedItemsCount,
                    RejectedItemsCount: report.RejectedItemsCount,
                    EmptyCellCount: report.EmptyCellCount);
            })
            .ToArray();
    }

    private static IReadOnlyList<string> NormalizeWarnings(IReadOnlyList<string>? warnings)
    {
        return warnings?.ToArray() ?? Array.Empty<string>();
    }

    private static string CreateKey(DatasetPreparationSourceReportDto sourceReport)
    {
        return CreateKey(sourceReport.Name, sourceReport.Type);
    }

    private static string CreateKey(string name, string type)
    {
        return $"{name}::{type}";
    }
}
