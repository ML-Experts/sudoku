using Sudoku.Application.ModelsActive;
using Sudoku.Application.ModelsRegistry;

namespace Application.Tests;

public sealed class GetActiveModelQueryHandlerTests
{
    [Fact]
    public async Task Handle_ReturnsNoActiveModel_WhenPointerDoesNotExist()
    {
        var handler = new GetActiveModelQueryHandler(
            new StubActiveModelResolver(null));

        var result = await handler.Handle(new GetActiveModelQuery(), CancellationToken.None);

        Assert.Null(result.ActiveModel);
    }

    [Fact]
    public async Task Handle_ReturnsActiveModel_WhenPointerAndManifestAreValid()
    {
        var updatedAtUtc = DateTimeOffset.Parse("2026-05-03T11:05:00Z");
        var manifest = CreateManifest("trained-model");
        var handler = new GetActiveModelQueryHandler(
            new StubActiveModelResolver(new ResolvedActiveModelDto(
                Pointer: new ActiveModelPointerDto(
                ModelName: "trained-model",
                RegistryRelativePath: "../registry/trained-model",
                SetBy: "backend",
                UpdatedAtUtc: updatedAtUtc),
                Manifest: manifest,
                ManifestPath: "/tmp/models/registry/trained-model/model.json",
                PrimaryArtifactPath: "/tmp/models/registry/trained-model/artifacts/model.pt")));

        var result = await handler.Handle(new GetActiveModelQuery(), CancellationToken.None);

        Assert.NotNull(result.ActiveModel);
        Assert.Equal("trained-model", result.ActiveModel.ModelName);
        Assert.Equal("default-28x28-v1", result.ActiveModel.InputProfile);
        Assert.True(result.ActiveModel.CanUseForInference);
        Assert.Equal(updatedAtUtc, result.ActiveModel.ActivatedAtUtc);
    }

    private static RegistryModelManifestDto CreateManifest(
        string name,
        bool canUseForInference = true,
        string primaryArtifactRelativePath = "artifacts/model.pt")
    {
        return new RegistryModelManifestDto(
            Name: name,
            DisplayName: name,
            SourceType: "training",
            SourceRunName: name,
            ParentModelName: "cnn-bootstrap",
            TrainingMode: "fineTuning",
            Framework: "pytorch",
            ArchitectureType: "cnn",
            ArchitectureFamily: "sudoku-digit-classifier",
            ArchitectureNumClasses: 10,
            ArchitectureInputChannels: 1,
            ArchitectureInputHeight: 28,
            ArchitectureInputWidth: 28,
            InputProfile: "default-28x28-v1",
            TrainingProfileName: "default-training",
            AugmentationProfileName: "default-augmentation",
            CreatedAtUtc: DateTimeOffset.Parse("2026-05-03T10:05:00Z"),
            CanStartTraining: true,
            CanUseForInference: canUseForInference,
            PrimaryArtifactRelativePath: primaryArtifactRelativePath,
            ArtifactFormat: "pytorch-state-dict",
            Warnings: Array.Empty<string>());
    }

    private sealed class StubActiveModelResolver : IActiveModelResolver
    {
        private readonly ResolvedActiveModelDto? _resolvedActiveModel;

        public StubActiveModelResolver(ResolvedActiveModelDto? resolvedActiveModel)
        {
            _resolvedActiveModel = resolvedActiveModel;
        }

        public Task<ResolvedActiveModelDto?> ResolveForInferenceAsync(CancellationToken cancellationToken = default)
        {
            return Task.FromResult(_resolvedActiveModel);
        }
    }
}
