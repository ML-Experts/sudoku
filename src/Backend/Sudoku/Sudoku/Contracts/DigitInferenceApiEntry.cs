namespace Sudoku.Contracts
{
    public class DigitInferenceApiEntry
    {
        public ImageApiEntry Image { get; set; } = null!;
        public double EmptyCellDarkPixelRatioThreshold { get; set; }
        public double EmptyCellInnerMarginRatio { get; set; }
        public double CenterAreaRatio { get; set; }
        public double MinComponentAreaRatio { get; set; }
        public double LineArtifactMinSpanRatio { get; set; }
        public double LineArtifactMaxThicknessRatio { get; set; }
    }
}
