using System.Net;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Options;
using Sudoku.Application.Ml;
using Sudoku.Application.SudokuOverlay;
using Sudoku.Infrastructure.Configuration;
using Sudoku.Infrastructure.Ml;
using Sudoku.Models.Images;
using Sudoku.Models.Sudoku;

namespace Application.Tests;

public sealed class MlImageProcessingHttpClientTests
{
    [Fact]
    public async Task RenderOverlayCellAsync_SendsPostToConfiguredPath()
    {
        var handler = new StubHttpMessageHandler(_ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(
                """{"mimeType":"image/png","base64":"CQgH"}""",
                Encoding.UTF8,
                "application/json")
        });
        var client = CreateClient(handler);

        var result = await client.RenderOverlayCellAsync(
            new RenderSudokuOverlayCellMlRequestDto(
                CellImage: new ImageContent("image/png", [1, 2, 3]),
                Digit: 4,
                CellPosition: new SudokuCellPosition(0, 2)),
            CancellationToken.None);

        Assert.Equal(HttpMethod.Post, handler.LastMethod);
        Assert.Equal("/ml/sudoku/overlay/cells", handler.LastPath);

        using var payloadDocument = JsonDocument.Parse(handler.LastContent!);
        Assert.Equal(4, payloadDocument.RootElement.GetProperty("digit").GetInt32());
        Assert.Equal(0, payloadDocument.RootElement.GetProperty("rowIndex").GetInt32());
        Assert.Equal(2, payloadDocument.RootElement.GetProperty("columnIndex").GetInt32());
        Assert.Equal("image/png", payloadDocument.RootElement.GetProperty("cellImage").GetProperty("mimeType").GetString());
        Assert.Equal("image/png", result.MimeType);
        Assert.Equal([9, 8, 7], result.Content);
    }

    [Fact]
    public async Task RenderOverlayCellAsync_MapsUnprocessableEntityToMlOperationFailed()
    {
        var handler = new StubHttpMessageHandler(_ => new HttpResponseMessage(HttpStatusCode.UnprocessableEntity)
        {
            Content = new StringContent(
                """{"errorType":"overlay_render_not_possible","message":"Nie można wyrenderować cyfry."}""",
                Encoding.UTF8,
                "application/json")
        });
        var client = CreateClient(handler);

        var exception = await Assert.ThrowsAsync<MlOperationFailedException>(() => client.RenderOverlayCellAsync(
            CreateRequest(),
            CancellationToken.None));

        Assert.Equal(RenderSudokuOverlayCellErrorTypes.OverlayRenderNotPossible, exception.ErrorType);
    }

    [Fact]
    public async Task RenderOverlayCellAsync_MapsServiceUnavailableToMlServiceUnavailable()
    {
        var handler = new StubHttpMessageHandler(_ => new HttpResponseMessage(HttpStatusCode.ServiceUnavailable)
        {
            Content = new StringContent(
                """{"errorType":"ml_unavailable","message":"Serwis ML jest niedostępny."}""",
                Encoding.UTF8,
                "application/json")
        });
        var client = CreateClient(handler);

        await Assert.ThrowsAsync<MlServiceUnavailableException>(() => client.RenderOverlayCellAsync(
            CreateRequest(),
            CancellationToken.None));
    }

    [Fact]
    public async Task RenderOverlayCellAsync_ThrowsMlOperationFailed_WhenMlReturnsInvalidBase64()
    {
        var handler = new StubHttpMessageHandler(_ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(
                """{"mimeType":"image/png","base64":"not-base64"}""",
                Encoding.UTF8,
                "application/json")
        });
        var client = CreateClient(handler);

        var exception = await Assert.ThrowsAsync<MlOperationFailedException>(() => client.RenderOverlayCellAsync(
            CreateRequest(),
            CancellationToken.None));

        Assert.Equal("ml_operation_failed", exception.ErrorType);
    }

    private static MlImageProcessingHttpClient CreateClient(HttpMessageHandler handler)
    {
        return new MlImageProcessingHttpClient(
            new HttpClient(handler)
            {
                BaseAddress = new Uri("http://127.0.0.1:8000")
            },
            Options.Create(new MlServiceOptions
            {
                BaseUrl = "http://127.0.0.1:8000",
                SudokuOverlayCellsPath = "/ml/sudoku/overlay/cells"
            }),
            NullLogger<MlImageProcessingHttpClient>.Instance);
    }

    private static RenderSudokuOverlayCellMlRequestDto CreateRequest()
    {
        return new RenderSudokuOverlayCellMlRequestDto(
            CellImage: new ImageContent("image/png", [1, 2, 3]),
            Digit: 4,
            CellPosition: null);
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
