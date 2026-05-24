using Sudoku.Models.Sudoku;

namespace Sudoku.Application.SudokuSolve;

public sealed record SudokuSolverStepDto(
    string EventType,
    int?[][] CurrentGrid,
    SudokuCellPosition Position,
    int? Digit);
