using System.ComponentModel.DataAnnotations;

namespace Sudoku.Application.Datasets;

public sealed class DatasetsPreparationOptions
{
    public const string SectionName = "DatasetsPreparation";

    [Required]
    public string BoardsSubdirectory { get; init; } = string.Empty;

    [Required]
    public string DigitsSubdirectory { get; init; } = string.Empty;

    [Required]
    public string ProcessedDatasetsDirectoryPath { get; init; } = string.Empty;

    [Required]
    public string TemporaryArtifactsDirectoryPath { get; init; } = string.Empty;

    [Required]
    public string DefaultPreprocessingProfile { get; init; } = string.Empty;

    [Required]
    public MixSplitRatiosOptions DefaultMixSplitRatios { get; init; } = new();

    public sealed class MixSplitRatiosOptions
    {
        [Range(0, 1)]
        public double Train { get; init; } = 0.8;

        [Range(0, 1)]
        public double Val { get; init; } = 0.1;

        [Range(0, 1)]
        public double Test { get; init; } = 0.1;
    }
}
