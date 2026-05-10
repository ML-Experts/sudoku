using System.Text.Json;
using MediatR;
using Sudoku.Application.Abstractions;
using Sudoku.Application.ModelsRegistry;

namespace Sudoku.Application.ModelsActive;

public sealed class GetActiveModelQueryHandler
    : IRequestHandler<GetActiveModelQuery, GetActiveModelQueryResultDto>
{
    private readonly IActiveModelPointerGateway _activeModelPointerGateway;
    private readonly IModelsRegistryGateway _modelsRegistryGateway;

    public GetActiveModelQueryHandler(
        IActiveModelPointerGateway activeModelPointerGateway,
        IModelsRegistryGateway modelsRegistryGateway)
    {
        _activeModelPointerGateway = activeModelPointerGateway;
        _modelsRegistryGateway = modelsRegistryGateway;
    }

    public async Task<GetActiveModelQueryResultDto> Handle(
        GetActiveModelQuery request,
        CancellationToken cancellationToken)
    {
        var pointer = await ResolvePointerAsync(cancellationToken);
        if (pointer is null)
        {
            return new GetActiveModelQueryResultDto(ActiveModel: null);
        }

        var modelName = ResolvePointerModelName(pointer);
        var model = await ResolveModelAsync(modelName, cancellationToken);
        ActiveModelActivationRules.EnsureCanUseForInference(model);
        ActiveModelActivationRules.EnsureActivatableManifest(model);

        return new GetActiveModelQueryResultDto(
            new ActiveModelDto(
                ModelName: model.Name,
                DisplayName: model.DisplayName,
                SourceType: model.SourceType,
                SourceRunName: model.SourceRunName,
                ParentModelName: model.ParentModelName,
                InputProfile: model.InputProfile,
                CanUseForInference: model.CanUseForInference,
                ActivatedAtUtc: pointer.UpdatedAtUtc));
    }

    private async Task<ActiveModelPointerDto?> ResolvePointerAsync(CancellationToken cancellationToken)
    {
        try
        {
            return await _activeModelPointerGateway.GetAsync(cancellationToken);
        }
        catch (JsonException exception)
        {
            throw new ActiveModelPointerInvalidException(
                modelName: null,
                "Wskaźnik aktywnego modelu jest uszkodzony albo ma niepoprawny format.",
                exception);
        }
        catch (Exception exception) when (exception is IOException
                                         or UnauthorizedAccessException
                                         or InvalidOperationException)
        {
            throw new ActiveModelPointerReadException(
                "Nie udało się odczytać wskaźnika aktywnego modelu.",
                exception);
        }
    }

    private static string ResolvePointerModelName(ActiveModelPointerDto pointer)
    {
        var failure = ActiveModelActivationRules.ValidateModelName(
            pointer.ModelName,
            nameof(ActiveModelPointerDto.ModelName));
        if (failure is not null)
        {
            throw new ActiveModelPointerInvalidException(
                pointer.ModelName,
                "Wskaźnik aktywnego modelu zawiera niepoprawną nazwę modelu.");
        }

        if (pointer.UpdatedAtUtc == default)
        {
            throw new ActiveModelPointerInvalidException(
                pointer.ModelName,
                "Wskaźnik aktywnego modelu nie zawiera poprawnej daty aktualizacji.");
        }

        return pointer.ModelName.Trim();
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
}
