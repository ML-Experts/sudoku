using MediatR;

namespace Sudoku.Application.ModelsRegistry;

public sealed record ListRegistryModelsQuery : IRequest<ListRegistryModelsQueryResultDto>;
