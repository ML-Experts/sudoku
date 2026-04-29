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
  message: string;
  progressChannelUrl: string | null;
};

export type TrainingRunProgressApiResponse = {
  percent: number | null;
  epoch: number | null;
  totalEpochs: number | null;
  trainLoss: number | null;
  validationLoss: number | null;
  trainAccuracy: number | null;
  validationAccuracy: number | null;
};

export type TrainingMetricsSummaryApiResponse = {
  accuracy: number | null;
  macroF1: number | null;
};

export type TrainingRunRealtimeApiResponse = {
  messageKind: string;
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
  seed: number;
  lastAcceptedSequence: number | null;
  lastEventType: string | null;
  progress: TrainingRunProgressApiResponse | null;
  metricsSummary: TrainingMetricsSummaryApiResponse | null;
  reportStatus: string | null;
  reportRelativePath: string | null;
  warnings: string[];
  cleanupWarnings: string[];
  failureReason: string | null;
};
