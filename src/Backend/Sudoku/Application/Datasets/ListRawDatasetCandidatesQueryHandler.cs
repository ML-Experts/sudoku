using MediatR;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;

namespace Sudoku.Application.Datasets;

public sealed class ListRawDatasetCandidatesQueryHandler
    : IRequestHandler<ListRawDatasetCandidatesQuery, ListRawDatasetCandidatesQueryResultDto>
{
    private const string DigitImagesSuffix = ".idx3-ubyte";
    private const string DigitLabelsSuffix = ".idx1-ubyte";

    private readonly IFileStorageGateway _fileStorageGateway;
    private readonly RawDatasetsStorageOptions _rawDatasetsStorageOptions;

    public ListRawDatasetCandidatesQueryHandler(
        IFileStorageGateway fileStorageGateway,
        IOptions<RawDatasetsStorageOptions> rawDatasetsStorageOptions)
    {
        _fileStorageGateway = fileStorageGateway;
        _rawDatasetsStorageOptions = rawDatasetsStorageOptions.Value;
    }

    public async Task<ListRawDatasetCandidatesQueryResultDto> Handle(
        ListRawDatasetCandidatesQuery request,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var boardCandidatesTask = LoadBoardCandidatesAsync(cancellationToken);
        var digitCandidatesTask = LoadDigitCandidatesAsync(cancellationToken);
        await Task.WhenAll(boardCandidatesTask, digitCandidatesTask);

        var items = boardCandidatesTask.Result
            .Concat(digitCandidatesTask.Result)
            .OrderBy(item => item.Type, StringComparer.Ordinal)
            .ThenBy(item => item.Name, StringComparer.Ordinal)
            .ToArray();

        return new ListRawDatasetCandidatesQueryResultDto(Items: items);
    }

    private async Task<IReadOnlyList<ListRawDatasetCandidateItemDto>> LoadBoardCandidatesAsync(
        CancellationToken cancellationToken)
    {
        var directories = await _fileStorageGateway.ListDirectoriesAsync(
            _rawDatasetsStorageOptions.BoardsSubdirectory,
            cancellationToken);

        return directories
            .Where(directory => !IsHiddenPathName(directory.Name))
            .Select(directory => new ListRawDatasetCandidateItemDto(
                Name: directory.Name,
                Type: "board"))
            .ToArray();
    }

    private async Task<IReadOnlyList<ListRawDatasetCandidateItemDto>> LoadDigitCandidatesAsync(
        CancellationToken cancellationToken)
    {
        var files = await _fileStorageGateway.ListFilesAsync(
            _rawDatasetsStorageOptions.DigitsSubdirectory,
            cancellationToken);

        var imagePrefixes = new HashSet<string>(StringComparer.Ordinal);
        var labelPrefixes = new HashSet<string>(StringComparer.Ordinal);

        foreach (var file in files)
        {
            var fileName = file.Name;
            if (IsHiddenPathName(fileName))
            {
                continue;
            }

            if (TryExtractPrefix(fileName, DigitImagesSuffix, out var imagePrefix))
            {
                imagePrefixes.Add(imagePrefix);
                continue;
            }

            if (TryExtractPrefix(fileName, DigitLabelsSuffix, out var labelPrefix))
            {
                labelPrefixes.Add(labelPrefix);
            }
        }

        return imagePrefixes
            .Intersect(labelPrefixes, StringComparer.Ordinal)
            .Where(prefix => !string.IsNullOrWhiteSpace(prefix))
            .Select(prefix => new ListRawDatasetCandidateItemDto(
                Name: prefix,
                Type: "digit"))
            .OrderBy(item => item.Name, StringComparer.Ordinal)
            .ToArray();
    }

    private static bool TryExtractPrefix(
        string fileName,
        string suffix,
        out string prefix)
    {
        prefix = string.Empty;

        if (!fileName.EndsWith(suffix, StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }

        prefix = fileName[..^suffix.Length];
        return true;
    }

    private static bool IsHiddenPathName(string value)
    {
        return value.StartsWith(".", StringComparison.Ordinal);
    }
}
