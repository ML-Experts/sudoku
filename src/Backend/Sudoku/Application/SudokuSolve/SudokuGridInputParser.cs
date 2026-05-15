using System.Text.Json;

namespace Sudoku.Application.SudokuSolve;

internal static class SudokuGridInputParser
{
    public static bool TryParse(
        JsonElement? gridElement,
        out int?[][]? grid,
        out string errorType,
        out string message)
    {
        grid = null;
        errorType = SolveSudokuErrorTypes.InvalidRequest;
        message = "Pole 'grid' jest wymagane.";

        if (!gridElement.HasValue
            || gridElement.Value.ValueKind is JsonValueKind.Undefined or JsonValueKind.Null)
        {
            return false;
        }

        if (gridElement.Value.ValueKind != JsonValueKind.Array)
        {
            errorType = SolveSudokuErrorTypes.GridShapeInvalid;
            message = "Pole 'grid' musi być tablicą 9x9.";
            return false;
        }

        var rows = gridElement.Value.EnumerateArray().ToArray();
        if (rows.Length != 9)
        {
            errorType = SolveSudokuErrorTypes.GridShapeInvalid;
            message = "Pole 'grid' musi zawierać dokładnie 9 wierszy.";
            return false;
        }

        var parsedGrid = new int?[9][];
        for (var rowIndex = 0; rowIndex < rows.Length; rowIndex++)
        {
            var row = rows[rowIndex];
            if (row.ValueKind != JsonValueKind.Array)
            {
                errorType = SolveSudokuErrorTypes.GridShapeInvalid;
                message = $"Wiersz {rowIndex + 1} planszy musi być tablicą.";
                return false;
            }

            var cells = row.EnumerateArray().ToArray();
            if (cells.Length != 9)
            {
                errorType = SolveSudokuErrorTypes.GridShapeInvalid;
                message = $"Wiersz {rowIndex + 1} planszy musi zawierać dokładnie 9 kolumn.";
                return false;
            }

            parsedGrid[rowIndex] = new int?[9];
            for (var columnIndex = 0; columnIndex < cells.Length; columnIndex++)
            {
                var cell = cells[columnIndex];
                if (cell.ValueKind == JsonValueKind.Null)
                {
                    parsedGrid[rowIndex][columnIndex] = null;
                    continue;
                }

                if (cell.ValueKind != JsonValueKind.Number || !cell.TryGetInt32(out var digit))
                {
                    errorType = SolveSudokuErrorTypes.GridValueOutOfRange;
                    message = $"Komórka [{rowIndex + 1},{columnIndex + 1}] musi mieć wartość null albo liczbę całkowitą 1..9.";
                    return false;
                }

                if (digit is < 1 or > 9)
                {
                    errorType = SolveSudokuErrorTypes.GridValueOutOfRange;
                    message = $"Komórka [{rowIndex + 1},{columnIndex + 1}] musi zawierać cyfrę z zakresu 1..9 albo null.";
                    return false;
                }

                parsedGrid[rowIndex][columnIndex] = digit;
            }
        }

        grid = parsedGrid;
        return true;
    }
}
