using MediatR;
using Microsoft.Extensions.Options;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Ml;
using Sudoku.Application.ModelsActive;
using Sudoku.Models.Images;
using Sudoku.Models.Sudoku;

namespace Sudoku.Application.Sudoku;

public sealed class InferSudokuCellDigitCommandHandler
    : IRequestHandler<InferSudokuCellDigitCommand, InferSudokuCellDigitCommandResultDto>
{
    private readonly IMlImageProcessingGateway _mlImageProcessingGateway;
    private readonly IActiveModelResolver _activeModelResolver;
    private readonly SudokuCellsInferenceOptions _options;

    public InferSudokuCellDigitCommandHandler(
        IMlImageProcessingGateway mlImageProcessingGateway,
        IActiveModelResolver activeModelResolver,
        IOptions<SudokuCellsInferenceOptions> options)
    {
        _mlImageProcessingGateway = mlImageProcessingGateway;
        _activeModelResolver = activeModelResolver;
        _options = options.Value;
    }

    public async Task<InferSudokuCellDigitCommandResultDto> Handle(
        InferSudokuCellDigitCommand request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.MimeType) || string.IsNullOrWhiteSpace(request.Base64))
        {
            throw new InvalidOperationException("InferSudokuCellDigitCommand must be validated before handler execution.");
        }

        var resolvedActiveModel = await _activeModelResolver.ResolveForInferenceAsync(cancellationToken)
                                  ?? throw new ActiveModelNotConfiguredException();

        byte[] imageBytes;
        try
        {
            imageBytes = Convert.FromBase64String(request.Base64);
        }
        catch (FormatException)
        {
            throw new InvalidOperationException("InferSudokuCellDigitCommand contains invalid Base64 payload.");
        }

        var image = new ImageContent(
            MimeType: request.MimeType,
            Content: imageBytes);
        var mlRequest = BuildMlRequest(image, resolvedActiveModel);
        var mlResult = await _mlImageProcessingGateway.InferDigitAsync(mlRequest, cancellationToken);

        DigitInferenceResult result;
        try
        {
            result = new DigitInferenceResult(mlResult.Digit);
        }
        catch (ArgumentOutOfRangeException)
        {
            throw new MlOperationFailedException(
                InferSudokuCellDigitErrorTypes.MlInvalidResponse,
                "Serwis ML zwrócił cyfrę spoza dozwolonego zakresu 1..9 albo null.");
        }

        return new InferSudokuCellDigitCommandResultDto(result.Digit);
    }

    private InferSudokuCellDigitMlRequestDto BuildMlRequest(
        ImageContent image,
        ResolvedActiveModelDto resolvedActiveModel)
    {
        return new InferSudokuCellDigitMlRequestDto(
            Image: image,
            ActiveModel: new InferSudokuCellDigitMlActiveModelDto(
                Name: resolvedActiveModel.Manifest.Name,
                ManifestPath: resolvedActiveModel.ManifestPath,
                PrimaryArtifactPath: resolvedActiveModel.PrimaryArtifactPath,
                InputProfile: resolvedActiveModel.Manifest.InputProfile),
            ResolvedConfiguration: new InferSudokuCellDigitMlResolvedConfigurationDto(
                InferenceProfileName: _options.InferenceProfileName,
                EmptyCellInnerMarginRatio: _options.EmptyCellInnerMarginRatio,
                EmptyCellDarkPixelRatioThreshold: _options.EmptyCellDarkPixelRatioThreshold));
    }
}
