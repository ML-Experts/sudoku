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
