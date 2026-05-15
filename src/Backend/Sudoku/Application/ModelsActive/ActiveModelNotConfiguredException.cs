namespace Sudoku.Application.ModelsActive;

public sealed class ActiveModelNotConfiguredException : Exception
{
    public ActiveModelNotConfiguredException()
        : base("Aktywny model inferencyjny nie jest skonfigurowany.")
    {
    }
}
