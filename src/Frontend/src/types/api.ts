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

export type ErrorApiResponse = {
  errorType: string;
  message: string;
};

export type RegistryModelListItemApiResponse = {
  name: string;
  displayName: string;
  sourceType: string;
  sourceRunName: string | null;
  parentModelName: string | null;
  trainingMode: string;
  inputProfile: string;
  trainingProfileName: string;
  augmentationProfileName: string;
  createdAtUtc: string;
  canStartTraining: boolean;
  canUseForInference: boolean;
};

export type RegistryModelsListApiResponse = {
  items: RegistryModelListItemApiResponse[];
  totalCount: number;
};

export type ProcessedDatasetSampleCountsApiResponse = {
  train: number;
  val: number;
  test: number;
};

export type ProcessedDatasetListItemApiResponse = {
  name: string;
  fileName: string;
  preprocessingProfile: string;
  createdAtUtc: string;
  sampleCounts: ProcessedDatasetSampleCountsApiResponse;
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
