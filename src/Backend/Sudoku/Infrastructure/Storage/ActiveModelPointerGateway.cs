using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.ModelsActive;
using Sudoku.Application.Storage;

namespace Sudoku.Infrastructure.Storage;

public sealed class ActiveModelPointerGateway : IActiveModelPointerGateway
{
    private const string PointerFileName = "inference.json";

    private static readonly JsonSerializerOptions JsonSerializerOptions = new(JsonSerializerDefaults.Web)
    {
        WriteIndented = true
    };

    private readonly IFileStorageGateway _fileStorageGateway;
    private readonly ModelsActiveStorageOptions _modelsActiveStorageOptions;

    public ActiveModelPointerGateway(
        IFileStorageGateway fileStorageGateway,
        IOptions<ModelsActiveStorageOptions> modelsActiveStorageOptions)
    {
        _fileStorageGateway = fileStorageGateway;
        _modelsActiveStorageOptions = modelsActiveStorageOptions.Value;
    }

    public async Task<ActiveModelPointerDto?> GetAsync(
        CancellationToken cancellationToken = default)
    {
        try
        {
            await using var stream = await _fileStorageGateway.OpenReadAsync(
                _modelsActiveStorageOptions.ActiveDirectoryPath,
                PointerFileName,
                cancellationToken);

            return await JsonSerializer.DeserializeAsync<ActiveModelPointerDto>(
                stream,
                JsonSerializerOptions,
                cancellationToken);
        }
        catch (FileStorageItemNotFoundException)
        {
            return null;
        }
    }

    public async Task ReplaceAsync(
        ActiveModelPointerDto pointer,
        CancellationToken cancellationToken = default)
    {
        var payload = new
        {
            modelName = pointer.ModelName,
            registryRelativePath = pointer.RegistryRelativePath,
            setBy = pointer.SetBy,
            updatedAtUtc = pointer.UpdatedAtUtc
        };

        var json = JsonSerializer.Serialize(payload, JsonSerializerOptions);
        await using var content = new MemoryStream(Encoding.UTF8.GetBytes(json));

        await _fileStorageGateway.ReplaceAsync(
            _modelsActiveStorageOptions.ActiveDirectoryPath,
            PointerFileName,
            content,
            cancellationToken);
    }
}
