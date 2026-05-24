namespace Sudoku.Models.Sudoku;

public readonly record struct SudokuCellPosition
{
    public SudokuCellPosition(int row, int column)
    {
        if (row is < 0 or > 8)
        {
            throw new ArgumentOutOfRangeException(nameof(row), "Wiersz musi mieścić się w zakresie 0..8.");
        }

        if (column is < 0 or > 8)
        {
            throw new ArgumentOutOfRangeException(nameof(column), "Kolumna musi mieścić się w zakresie 0..8.");
        }

        Row = row;
        Column = column;
    }

    public int Row { get; }

    public int Column { get; }
}
