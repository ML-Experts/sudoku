namespace Sudoku.Models.Sudoku;

public sealed class SudokuGrid
{
    private const int GridSize = 9;

    private readonly int?[,] _cells = new int?[GridSize, GridSize];
    private readonly bool[,] _lockedCells = new bool[GridSize, GridSize];

    public SudokuGrid(int?[][] grid)
    {
        ArgumentNullException.ThrowIfNull(grid);

        if (grid.Length != GridSize)
        {
            throw new ArgumentException("Plansza sudoku musi zawierać dokładnie 9 wierszy.", nameof(grid));
        }

        for (var row = 0; row < GridSize; row++)
        {
            var sourceRow = grid[row] ?? throw new ArgumentException(
                "Każdy wiersz planszy sudoku musi istnieć.",
                nameof(grid));

            if (sourceRow.Length != GridSize)
            {
                throw new ArgumentException(
                    "Każdy wiersz planszy sudoku musi zawierać dokładnie 9 kolumn.",
                    nameof(grid));
            }

            for (var column = 0; column < GridSize; column++)
            {
                var digit = sourceRow[column];
                if (digit is < 1 or > 9)
                {
                    throw new ArgumentOutOfRangeException(
                        nameof(grid),
                        "Komórki planszy sudoku muszą mieć wartości null albo cyfry 1..9.");
                }

                _cells[row, column] = digit;
                _lockedCells[row, column] = digit.HasValue;
            }
        }
    }

    public int? GetDigit(SudokuCellPosition position)
    {
        return _cells[position.Row, position.Column];
    }

    public bool IsLocked(SudokuCellPosition position)
    {
        return _lockedCells[position.Row, position.Column];
    }

    public bool IsEmpty(SudokuCellPosition position)
    {
        return !_cells[position.Row, position.Column].HasValue;
    }

    public void SetSolverDigit(SudokuCellPosition position, int digit)
    {
        EnsureSolverCanMutate(position);

        if (digit is < 1 or > 9)
        {
            throw new ArgumentOutOfRangeException(nameof(digit), "Cyfra solvera musi mieścić się w zakresie 1..9.");
        }

        _cells[position.Row, position.Column] = digit;
    }

    public void ClearSolverDigit(SudokuCellPosition position)
    {
        EnsureSolverCanMutate(position);
        _cells[position.Row, position.Column] = null;
    }

    public IEnumerable<SudokuCellPosition> EnumerateEmptyCells()
    {
        for (var row = 0; row < GridSize; row++)
        {
            for (var column = 0; column < GridSize; column++)
            {
                if (!_cells[row, column].HasValue)
                {
                    yield return new SudokuCellPosition(row, column);
                }
            }
        }
    }

    public int?[][] ToJaggedArray()
    {
        var snapshot = new int?[GridSize][];
        for (var row = 0; row < GridSize; row++)
        {
            snapshot[row] = new int?[GridSize];
            for (var column = 0; column < GridSize; column++)
            {
                snapshot[row][column] = _cells[row, column];
            }
        }

        return snapshot;
    }

    private void EnsureSolverCanMutate(SudokuCellPosition position)
    {
        if (_lockedCells[position.Row, position.Column])
        {
            throw new InvalidOperationException("Solver nie może modyfikować cyfr wejściowych.");
        }
    }
}
