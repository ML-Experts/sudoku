using MediatR;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Ml;
using Sudoku.Models.Images;

namespace Sudoku.Application.Examples;

public sealed class PreprocessExampleCellsCommandHandler : IRequestHandler<PreprocessExampleCellsCommand, PreprocessCellsResultDto>
{
    private const string InvalidCellsGridErrorType = "invalid_cells_grid";

    private readonly IMlImageProcessingGateway _mlImageProcessingGateway;

    public PreprocessExampleCellsCommandHandler(IMlImageProcessingGateway mlImageProcessingGateway)
    {
        _mlImageProcessingGateway = mlImageProcessingGateway;
    }

    public async Task<PreprocessCellsResultDto> Handle(
        PreprocessExampleCellsCommand request,
        CancellationToken cancellationToken)
    {
        var sourceImage = InlineImagePayloadMapper.MapToImageContent(request.MimeType, request.Base64);
        var extractedCellsGrid = await _mlImageProcessingGateway.ExtractCellsAsync(sourceImage, cancellationToken);

        EnsureNineByNineGrid(extractedCellsGrid);

        return new PreprocessCellsResultDto(Cells: extractedCellsGrid);
    }

    private static void EnsureNineByNineGrid(CellsGrid cellsGrid)
    {
        if (cellsGrid.Cells.Count != CellsGrid.GridSize)
        {
            throw new MlOperationFailedException(
                InvalidCellsGridErrorType,
                "Serwis ML zwrócił nieprawidłowy wymiar siatki komórek. Wymagane jest dokładnie 9 wierszy.");
        }

        if (cellsGrid.Cells.Any(row => row.Count != CellsGrid.GridSize))
        {
            throw new MlOperationFailedException(
                InvalidCellsGridErrorType,
                "Serwis ML zwrócił nieprawidłowy wymiar siatki komórek. Każdy wiersz musi zawierać dokładnie 9 komórek.");
        }
    }
}
