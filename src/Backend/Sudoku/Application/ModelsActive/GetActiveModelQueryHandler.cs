using MediatR;

namespace Sudoku.Application.ModelsActive;

public sealed class GetActiveModelQueryHandler
    : IRequestHandler<GetActiveModelQuery, GetActiveModelQueryResultDto>
{
    private readonly IActiveModelResolver _activeModelResolver;

    public GetActiveModelQueryHandler(
        IActiveModelResolver activeModelResolver)
    {
        _activeModelResolver = activeModelResolver;
    }

    public async Task<GetActiveModelQueryResultDto> Handle(
        GetActiveModelQuery request,
        CancellationToken cancellationToken)
    {
        var resolvedActiveModel = await _activeModelResolver.ResolveForInferenceAsync(cancellationToken);
        if (resolvedActiveModel is null)
        {
            return new GetActiveModelQueryResultDto(ActiveModel: null);
        }

        return new GetActiveModelQueryResultDto(
            new ActiveModelDto(
                ModelName: resolvedActiveModel.Manifest.Name,
                DisplayName: resolvedActiveModel.Manifest.DisplayName,
                SourceType: resolvedActiveModel.Manifest.SourceType,
                SourceRunName: resolvedActiveModel.Manifest.SourceRunName,
                ParentModelName: resolvedActiveModel.Manifest.ParentModelName,
                InputProfile: resolvedActiveModel.Manifest.InputProfile,
                CanUseForInference: resolvedActiveModel.Manifest.CanUseForInference,
                ActivatedAtUtc: resolvedActiveModel.Pointer.UpdatedAtUtc));
    }
}
