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

export type CellsGridApiResponse = {
  cells: ImageApiResponse[][];
};

export type DigitInferenceApiResponse = {
  digit: number | null;
};

export type SolveSudokuApiEntry = {
  grid: (number | null)[][];
};

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

export type CreateTrainingRunApiEntry = {
  baseModelName: string;
  processedDatasetName: string;
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
