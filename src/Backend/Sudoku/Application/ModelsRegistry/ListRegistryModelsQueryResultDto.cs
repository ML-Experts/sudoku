namespace Sudoku.Application.ModelsRegistry;

public sealed record ListRegistryModelsQueryResultDto(
    IReadOnlyList<RegistryModelListItemDto> Items,
    int TotalCount);
