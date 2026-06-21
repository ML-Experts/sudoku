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

public sealed class MlDatasetPreparationsHttpClientTests
{
    [Fact]
    public async Task CreateAsync_SendsPostToConfiguredPath()
    {
        var handler = new StubHttpMessageHandler(_ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(
                """
                {"preparationName":"preparation-001","createdAtUtc":"2026-06-19T18:42:11Z","status":"completed","sourceReports":[{"name":"v1_training","type":"board","preparedItemsCount":24,"rejectedItemsCount":2,"emptyCellCount":3}],"warnings":["ml_warning"]}
                """,
                Encoding.UTF8,
                "application/json")
        });
        var client = CreateClient(handler);

        var result = await client.CreateAsync(
            new CreateDatasetPreparationMlRequestDto(
                PreparationName: "preparation-001",
                Sources: [new CreateDatasetPreparationMlSourceDto("v1_training", "board")]),
            CancellationToken.None);

        Assert.Equal(HttpMethod.Post, handler.LastMethod);
        Assert.Equal("/ml/datasets/preparations", handler.LastPath);

        using var payloadDocument = JsonDocument.Parse(handler.LastContent!);
        Assert.Equal("preparation-001", payloadDocument.RootElement.GetProperty("preparationName").GetString());
        Assert.Equal("v1_training", payloadDocument.RootElement.GetProperty("sources")[0].GetProperty("name").GetString());
        Assert.Single(result.SourceReports);
        Assert.Equal(24, result.SourceReports[0].PreparedItemsCount);
    }

    [Fact]
    public async Task CreateAsync_MapsUnprocessableEntityToMlOperationFailed()
    {
        var handler = new StubHttpMessageHandler(_ => new HttpResponseMessage(HttpStatusCode.UnprocessableEntity)
        {
            Content = new StringContent(
                """{"errorType":"dataset_source_invalid","message":"Zródło jest nieprawidłowe."}""",
                Encoding.UTF8,
                "application/json")
        });
        var client = CreateClient(handler);

        var exception = await Assert.ThrowsAsync<MlOperationFailedException>(() => client.CreateAsync(
            new CreateDatasetPreparationMlRequestDto(
                PreparationName: "preparation-001",
                Sources: [new CreateDatasetPreparationMlSourceDto("v1_training", "board")]),
            CancellationToken.None));

        Assert.Equal("dataset_source_invalid", exception.ErrorType);
    }

    [Fact]
    public async Task CreateAsync_MapsServiceUnavailableToMlServiceUnavailable()
    {
        var handler = new StubHttpMessageHandler(_ => new HttpResponseMessage(HttpStatusCode.ServiceUnavailable)
        {
            Content = new StringContent(
                """{"errorType":"ml_unavailable","message":"Serwis ML jest niedostępny."}""",
                Encoding.UTF8,
                "application/json")
        });
        var client = CreateClient(handler);

        await Assert.ThrowsAsync<MlServiceUnavailableException>(() => client.CreateAsync(
            new CreateDatasetPreparationMlRequestDto(
                PreparationName: "preparation-001",
                Sources: [new CreateDatasetPreparationMlSourceDto("v1_training", "board")]),
            CancellationToken.None));
    }

    private static MlDatasetPreparationsHttpClient CreateClient(HttpMessageHandler handler)
    {
        return new MlDatasetPreparationsHttpClient(
            new HttpClient(handler)
            {
                BaseAddress = new Uri("http://127.0.0.1:8000")
            },
            Options.Create(new MlServiceOptions
            {
                BaseUrl = "http://127.0.0.1:8000",
                DatasetPreparationsPath = "/ml/datasets/preparations"
            }),
            NullLogger<MlDatasetPreparationsHttpClient>.Instance);
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
