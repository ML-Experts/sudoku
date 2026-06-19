namespace Sudoku.Application.Datasets;

public sealed record GetDatasetPreparationBoardImageQueryResultDto(
    string MimeType,
    string Base64);
