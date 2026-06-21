export type SolveCellInferenceDefaults = {
  emptyCellDarkPixelRatioThreshold: number;
  emptyCellInnerMarginRatio: number;
  centerAreaRatio: number;
  minComponentAreaRatio: number;
  lineArtifactMinSpanRatio: number;
  lineArtifactMaxThicknessRatio: number;
  emptyCellMinSegmentLengthPx: number;
  emptyCellFilteredSegmentCountThreshold: number;
};

export const solveCellInferenceDefaults: SolveCellInferenceDefaults = {
  emptyCellDarkPixelRatioThreshold: 0.02,
  emptyCellInnerMarginRatio: 0.12,
  centerAreaRatio: 0.5,
  minComponentAreaRatio: 0.055,
  lineArtifactMinSpanRatio: 0.4,
  lineArtifactMaxThicknessRatio: 0.08,
  emptyCellMinSegmentLengthPx: 8,
  emptyCellFilteredSegmentCountThreshold: 2,
};
