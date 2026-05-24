namespace Sudoku.Application.Trainings;

public sealed class TrainingProfileMismatchException : Exception
{
    public TrainingProfileMismatchException(string modelInputProfile, string datasetPreprocessingProfile)
        : base("Profil wejściowy modelu bazowego nie jest zgodny z profilem preprocessingu datasetu.")
    {
        ModelInputProfile = modelInputProfile;
        DatasetPreprocessingProfile = datasetPreprocessingProfile;
    }

    public string ModelInputProfile { get; }

    public string DatasetPreprocessingProfile { get; }
}
