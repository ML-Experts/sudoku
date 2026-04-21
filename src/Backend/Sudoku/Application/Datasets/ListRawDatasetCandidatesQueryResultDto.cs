namespace Sudoku.Application.Datasets;

public sealed record ListRawDatasetCandidatesQueryResultDto(
    IReadOnlyList<ListRawDatasetCandidateItemDto> Items);
