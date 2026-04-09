namespace Sudoku.Models.Images;

public sealed class CellsGrid
{
    public const int GridSize = 9;

    public CellsGrid(IReadOnlyList<IReadOnlyList<ImageContent>> cells)
    {
        ArgumentNullException.ThrowIfNull(cells);

        if (cells.Count != GridSize)
        {
            throw new ArgumentException(
                $"Siatka komórek musi zawierać dokładnie {GridSize} wierszy.",
                nameof(cells));
        }

        var normalizedCells = new ImageContent[GridSize][];

        for (var rowIndex = 0; rowIndex < GridSize; rowIndex++)
        {
            var row = cells[rowIndex];
            ArgumentNullException.ThrowIfNull(row);

            if (row.Count != GridSize)
            {
                throw new ArgumentException(
                    $"Wiersz o indeksie {rowIndex} musi zawierać dokładnie {GridSize} komórek.",
                    nameof(cells));
            }

            normalizedCells[rowIndex] = row.ToArray();
        }

        Cells = normalizedCells;
    }

    public IReadOnlyList<IReadOnlyList<ImageContent>> Cells { get; }
}
