export type ExampleFileApiResponse = {
  name: string;
  contentType: string;
  sizeBytes: number;
  storedAtUtc: string;
};

export type ExamplesListApiResponse = {
  items: ExampleFileApiResponse[];
  totalCount: number;
};

export type ImageApiResponse = {
  mimeType: string;
  base64: string;
};

export type ImageApiEntry = {
  mimeType: string;
  base64: string;
};

export type RenderSudokuOverlayCellApiEntry = {
  cellImage: ImageApiEntry;
  digit: number;
  rowIndex?: number;
  columnIndex?: number;
};

export type CellsGridApiResponse = {
  cells: ImageApiResponse[][];
};

export type DigitInferenceApiResponse = {
  digit: number | null;
};

export type DigitInferenceApiEntry = {
  image: ImageApiEntry;
  emptyCellDarkPixelRatioThreshold: number;
  emptyCellInnerMarginRatio: number;
  centerAreaRatio: number;
  minComponentAreaRatio: number;
  lineArtifactMinSpanRatio: number;
  lineArtifactMaxThicknessRatio: number;
};

export type SudokuCellInferenceParametersApiEntry = Pick<
  DigitInferenceApiEntry,
  | "emptyCellDarkPixelRatioThreshold"
  | "emptyCellInnerMarginRatio"
  | "centerAreaRatio"
  | "minComponentAreaRatio"
  | "lineArtifactMinSpanRatio"
  | "lineArtifactMaxThicknessRatio"
>;

export type SolveSudokuApiEntry = {
  grid: (number | null)[][];
  solverStepDelayMs: number;
};

export type SolveSudokuParametersApiEntry = Pick<
  SolveSudokuApiEntry,
  "solverStepDelayMs"
>;

export type SolveSessionApiResponse = {
  solveSessionId: string;
  status: string;
  progressChannelUrl: string;
};

export type CancelSolveSessionApiResponse = {
  status: string | null;
  requestDisposition: string;
};

export type SolveProgressEventApiResponse = {
  eventType: string;
  solveSessionId: string;
  status: string;
  sequence: number;
  currentGrid: (number | null)[][];
  errorType: string | null;
  message: string | null;
};

export type AdminLoginApiEntry = {
  password: string;
};

export type AuthTokenApiResponse = {
  accessToken: string;
  tokenType: string;
  expiresAtUtc: string;
};

export type ErrorApiResponse = {
  errorType: string;
  message: string;
};

export type RawDatasetCandidateApiResponse = {
  name: string;
  type: string;
};

export type SelectedRawDatasetSourceApiEntry = {
  name: string;
  type: string;
  splits: string[];
};

export type CreateProcessedDatasetApiEntry = {
  name: string;
  sources: SelectedRawDatasetSourceApiEntry[];
};

export type SplitSampleCountsApiResponse = {
  train: number;
  val: number;
  test: number;
};

export type ProcessedDatasetSourceReportApiResponse = {
  name: string;
  type: string;
  processedSampleCount: number;
  includedSampleCount: number;
  emptyCellCount: number;
  rejectedSampleCount: number;
  warnings: string[];
};

export type ProcessedDatasetApiResponse = {
  name: string;
  fileName: string;
  preprocessingProfile: string;
  createdAtUtc: string;
  sources: SelectedRawDatasetSourceApiEntry[];
  sampleCounts: SplitSampleCountsApiResponse;
  sourceReports: ProcessedDatasetSourceReportApiResponse[];
  warnings: string[];
};

export type ProcessedDatasetListItemApiResponse = {
  name: string;
  fileName: string;
  preprocessingProfile: string;
  createdAtUtc: string;
  sampleCounts: SplitSampleCountsApiResponse;
};

export type ProcessedDatasetsListApiResponse = {
  items: ProcessedDatasetListItemApiResponse[];
  totalCount: number;
};

export type TrainingMetricsSummaryApiResponse = {
  accuracy: number | null;
  macroF1: number | null;
};

export type CreateTrainingRunParametersApiEntry = {
  epochs: number;
  learningRate: number;
  batchSize: number;
  earlyStoppingPatience: number;
  earlyStoppingMinDelta: number;
  warmupEpochs: number;
  lrSchedulerPatience: number;
  lrSchedulerFactor: number;
  fineTuningPolicy: string;
  useBestCheckpoint: boolean;
};

export type CreateTrainingRunApiEntry = {
  baseModelName: string;
  processedDatasetName: string;
  trainingParameters: CreateTrainingRunParametersApiEntry;
};

export type TrainingRunEffectiveParametersApiResponse = {
  epochs: number;
  learningRate: number;
  batchSize: number;
  earlyStoppingPatience: number;
  earlyStoppingMinDelta: number;
  warmupEpochs: number;
  lrSchedulerPatience: number;
  lrSchedulerFactor: number;
  fineTuningPolicy: string;
  useBestCheckpoint: boolean;
};

export type RegistryModelListItemApiResponse = {
  name: string;
  displayName: string;
  sourceType: string;
  sourceRunName: string | null;
  parentModelName: string | null;
  trainingMode: string;
  inputProfile: string;
  trainingProfileName: string | null;
  augmentationProfileName: string | null;
  createdAtUtc: string | null;
  canStartTraining: boolean;
  canUseForInference: boolean;
  warnings: string[];
};

export type RegistryModelsListApiResponse = {
  items: RegistryModelListItemApiResponse[];
  totalCount: number;
};

export type ActiveModelApiResponse = {
  modelName: string;
  displayName: string;
  sourceType: string;
  sourceRunName: string | null;
  parentModelName: string | null;
  inputProfile: string;
  canUseForInference: boolean;
  activatedAtUtc: string | null;
};

export type SetActiveModelApiEntry = {
  modelName: string;
};

export type TrainingRunApiResponse = {
  runName: string;
  status: string;
  createdAtUtc: string;
  baseModelName: string;
  producedModelName: string;
  processedDatasetName: string;
  trainingMode: string;
  trainingProfileName: string;
  augmentationProfileName: string;
  benchmarkName: string;
  seed: number;
  effectiveParameters: TrainingRunEffectiveParametersApiResponse | null;
  progressChannelUrl: string;
};

export type CancelTrainingRunApiResponse = {
  runName: string;
  status: string | null;
  requestDisposition: string;
  cancellationRequestedAtUtc: string | null;
};

export type TrainingRunProgressApiResponse = {
  percent: number | null;
  epochCurrent: number | null;
  epochTotal: number | null;
  etaSeconds: number | null;
  trainLoss?: number | null;
  validationLoss?: number | null;
  trainAccuracy?: number | null;
  validationAccuracy?: number | null;
};

export type TrainingRunListItemApiResponse = {
  runName: string;
  status: string;
  createdAtUtc: string;
  updatedAtUtc: string | null;
  startedAtUtc: string | null;
  finishedAtUtc: string | null;
  baseModelName: string;
  producedModelName: string;
  processedDatasetName: string;
  trainingMode: string;
  trainingProfileName: string;
  augmentationProfileName: string;
  benchmarkName: string;
  effectiveParameters: TrainingRunEffectiveParametersApiResponse | null;
  reportStatus: string | null;
  progress: TrainingRunProgressApiResponse | null;
  metricsSummary: TrainingMetricsSummaryApiResponse | null;
  warnings: string[];
};

export type TrainingRunsListApiResponse = {
  items: TrainingRunListItemApiResponse[];
  totalCount: number;
};

export type TrainingRunModelReferenceApiResponse = {
  name: string;
  displayName: string;
  sourceType: string;
  sourceRunName: string | null;
  parentModelName: string | null;
  inputProfile: string;
  canUseForInference: boolean;
  canStartTraining: boolean;
};

export type TrainingDatasetSampleCountsApiResponse = {
  train: number;
  val: number;
  test: number;
};

export type TrainingRunDatasetDetailsApiResponse = {
  processedDatasetName: string;
  preprocessingProfile: string | null;
  sampleCounts: TrainingDatasetSampleCountsApiResponse | null;
};

export type TrainingRunConfigurationApiResponse = {
  trainingMode: string;
  trainingProfileName: string;
  augmentationProfileName: string;
  benchmarkName: string;
  seed: number;
  effectiveParameters: TrainingRunEffectiveParametersApiResponse | null;
  sourceRevision: string | null;
};

export type TrainingReportSummaryApiResponse = {
  accuracy: number;
  precisionMacro: number;
  recallMacro: number;
  f1Macro: number;
  trainingDurationSeconds: number | null;
  averageInferenceTimeMs: number | null;
};

export type TrainingClassMetricApiResponse = {
  label: string;
  precision: number;
  recall: number;
  f1: number;
  support: number;
};

export type TrainingMetricHistoryPointApiResponse = {
  epoch: number;
  trainLoss: number | null;
  validationLoss: number | null;
  trainAccuracy: number | null;
  validationAccuracy: number | null;
};

export type TrainingConfusionMatrixApiResponse = {
  classNames: string[];
  matrix: number[][];
};

export type TrainingRunReportApiResponse = {
  status: string;
  summary: TrainingReportSummaryApiResponse | null;
  perClassMetrics: TrainingClassMetricApiResponse[];
  history: TrainingMetricHistoryPointApiResponse[];
  confusionMatrix: TrainingConfusionMatrixApiResponse | null;
};

export type TrainingRunDetailsApiResponse = {
  runName: string;
  status: string;
  stage: string | null;
  createdAtUtc: string;
  startedAtUtc: string | null;
  finishedAtUtc: string | null;
  baseModel: TrainingRunModelReferenceApiResponse;
  producedModel: TrainingRunModelReferenceApiResponse | null;
  dataset: TrainingRunDatasetDetailsApiResponse;
  configuration: TrainingRunConfigurationApiResponse;
  progress: TrainingRunProgressApiResponse | null;
  report: TrainingRunReportApiResponse;
  warnings: string[];
};

export type TrainingRunResultApiResponse = {
  producedModelName: string;
  reportStatus: string;
  canUseProducedModelForInference: boolean;
  primaryArtifactRelativePath: string;
  summaryRelativePath: string | null;
  metricsRelativePath: string | null;
  confusionMatrixRelativePath: string | null;
};

export type TrainingRunFailureApiResponse = {
  errorType: string;
  message: string;
  canUseProducedModelForInference: boolean;
};

export type TrainingRunSocketEventApiResponse = {
  eventType: string;
  sequence: number;
  runName: string;
  status: string;
  stage: string;
  occurredAtUtc: string;
  message: string | null;
  progress: TrainingRunProgressApiResponse | null;
  warnings: string[];
  result: TrainingRunResultApiResponse | null;
  failure: TrainingRunFailureApiResponse | null;
};
