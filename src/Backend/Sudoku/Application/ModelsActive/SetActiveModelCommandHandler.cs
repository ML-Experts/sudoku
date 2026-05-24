using System.Text.Json;
using MediatR;
using Sudoku.Application.Abstractions;
using Sudoku.Application.ModelsRegistry;

namespace Sudoku.Application.ModelsActive;

public sealed class SetActiveModelCommandHandler
    : IRequestHandler<SetActiveModelCommand, SetActiveModelCommandResultDto>
{
    private const string PointerSetBy = "backend";

    private readonly IModelsRegistryGateway _modelsRegistryGateway;
    private readonly IActiveModelPointerGateway _activeModelPointerGateway;
    private readonly TimeProvider _timeProvider;

    public SetActiveModelCommandHandler(
        IModelsRegistryGateway modelsRegistryGateway,
        IActiveModelPointerGateway activeModelPointerGateway,
        TimeProvider timeProvider)
    {
        _modelsRegistryGateway = modelsRegistryGateway;
        _activeModelPointerGateway = activeModelPointerGateway;
        _timeProvider = timeProvider;
    }

    public async Task<SetActiveModelCommandResultDto> Handle(
        SetActiveModelCommand request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.ModelName))
        {
            throw new InvalidOperationException("SetActiveModelCommand must be validated before handler execution.");
        }

        var modelName = request.ModelName.Trim();
        var model = await ResolveModelAsync(modelName, cancellationToken);
        ActiveModelActivationRules.EnsureCanUseForInference(model);
        ActiveModelActivationRules.EnsureActivatableManifest(model);

        var activatedAtUtc = _timeProvider.GetUtcNow();
        var pointer = new ActiveModelPointerDto(
            ModelName: model.Name,
            RegistryRelativePath: $"../registry/{model.Name}",
            SetBy: PointerSetBy,
            UpdatedAtUtc: activatedAtUtc);

        await ReplacePointerAsync(pointer, cancellationToken);

        return new SetActiveModelCommandResultDto(
            ModelName: model.Name,
            DisplayName: model.DisplayName,
            SourceType: model.SourceType,
            SourceRunName: model.SourceRunName,
            ParentModelName: model.ParentModelName,
            InputProfile: model.InputProfile,
            CanUseForInference: model.CanUseForInference,
            ActivatedAtUtc: activatedAtUtc);
    }

    private async Task<RegistryModelManifestDto> ResolveModelAsync(
        string modelName,
        CancellationToken cancellationToken)
    {
        try
        {
            var model = await _modelsRegistryGateway.GetByNameAsync(modelName, cancellationToken);
            return model ?? throw new ActiveModelNotFoundException(modelName);
        }
        catch (Exception exception) when (exception is InvalidDataException
                                         or InvalidOperationException
                                         or JsonException)
        {
            throw new ActiveModelManifestInvalidException(
                modelName,
                $"Manifest modelu {modelName} jest niekompletny albo niepoprawny.",
                exception);
        }
    }

    private async Task ReplacePointerAsync(
        ActiveModelPointerDto pointer,
        CancellationToken cancellationToken)
    {
        try
        {
            await _activeModelPointerGateway.ReplaceAsync(pointer, cancellationToken);
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidOperationException)
        {
            throw new ActiveModelPointerWriteException(
                pointer.ModelName,
                "Nie udało się zapisać wskaźnika aktywnego modelu.",
                exception);
        }
    }
}
