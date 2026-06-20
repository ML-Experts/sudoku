using System.Net;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Options;
using Sudoku.Application.Datasets;
using Sudoku.Application.Ml;
using Sudoku.Infrastructure.Configuration;
using Sudoku.Infrastructure.Ml;

namespace Application.Tests;

public sealed class MlDatasetsPreparationHttpClientTests
{
    [Fact]
    public async Task PrepareDatasetArtifactAsync_SendsPreparationNameToConfiguredPath()
    {
        var handler = new StubHttpMessageHandler(_ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(
                """
                {"sampleCounts":{"train":10,"val":2,"test":1},"sources":[{"name":"v1_training","requestedType":"board","detectedType":"board","processedSampleCount":13,"includedSampleCount":13,"emptyCellCount":0,"rejectedSampleCount":0,"warnings":[]}],"warnings":["ml_warning"]}
                """,
                Encoding.UTF8,
                "application/json")
        });
        var client = CreateClient(handler);

        var result = await client.PrepareDatasetArtifactAsync(
            new PrepareDatasetArtifactRequestDto(
                PreparationName: "preparation-001",
                DatasetName: "digits-v2",
                Sources:
                [
                    new PrepareDatasetSourceDto(
                        Name: "v1_training",
                        Type: "board",
                        SplitPolicy: new DatasetSplitPolicyDto(
                            Mode: "mix",
                            Ratios: new SplitRatiosDto(Train: 0.8, Val: 0.1, Test: 0.1),
                            GroupBy: "board"))
                ],
                PreprocessingProfile: "default-28x28-v1"),
            CancellationToken.None);

        Assert.Equal(HttpMethod.Post, handler.LastMethod);
        Assert.Equal("/ml/datasets/prepare", handler.LastPath);

        using var payloadDocument = JsonDocument.Parse(handler.LastContent!);
        Assert.Equal("preparation-001", payloadDocument.RootElement.GetProperty("preparationName").GetString());
        Assert.Equal("digits-v2", payloadDocument.RootElement.GetProperty("datasetName").GetString());
        Assert.Equal("v1_training", payloadDocument.RootElement.GetProperty("sources")[0].GetProperty("name").GetString());
        Assert.Equal(10, result.SampleCounts.Train);
    }

    [Fact]
    public async Task PrepareDatasetArtifactAsync_MapsInvalidJsonToMlServiceUnavailable()
    {
        var handler = new StubHttpMessageHandler(_ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(
                """{"sampleCounts":"broken"}""",
                Encoding.UTF8,
                "application/json")
        });
        var client = CreateClient(handler);

        await Assert.ThrowsAsync<MlServiceUnavailableException>(() => client.PrepareDatasetArtifactAsync(
            new PrepareDatasetArtifactRequestDto(
                PreparationName: "preparation-001",
                DatasetName: "digits-v2",
                Sources:
                [
                    new PrepareDatasetSourceDto(
                        Name: "v1_training",
                        Type: "board",
                        SplitPolicy: new DatasetSplitPolicyDto(
                            Mode: "mix",
                            Ratios: new SplitRatiosDto(Train: 0.8, Val: 0.1, Test: 0.1),
                            GroupBy: "board"))
                ],
                PreprocessingProfile: "default-28x28-v1"),
            CancellationToken.None));
    }

    private static MlDatasetsPreparationHttpClient CreateClient(HttpMessageHandler handler)
    {
        return new MlDatasetsPreparationHttpClient(
            new HttpClient(handler)
            {
                BaseAddress = new Uri("http://127.0.0.1:8000")
            },
            Options.Create(new MlServiceOptions
            {
                BaseUrl = "http://127.0.0.1:8000",
                PrepareDatasetPath = "/ml/datasets/prepare"
            }),
            NullLogger<MlDatasetsPreparationHttpClient>.Instance);
    }

    private sealed class StubHttpMessageHandler : HttpMessageHandler
    {
        private readonly Func<HttpRequestMessage, HttpResponseMessage> _responseFactory;

        public StubHttpMessageHandler(Func<HttpRequestMessage, HttpResponseMessage> responseFactory)
        {
            _responseFactory = responseFactory;
        }

        public string? LastContent { get; private set; }

        public HttpMethod? LastMethod { get; private set; }

        public string? LastPath { get; private set; }

        protected override Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken)
        {
            LastMethod = request.Method;
            LastPath = request.RequestUri?.AbsolutePath;
            LastContent = request.Content is null
                ? null
                : request.Content.ReadAsStringAsync(cancellationToken).GetAwaiter().GetResult();
            return Task.FromResult(_responseFactory(request));
        }
    }
}
