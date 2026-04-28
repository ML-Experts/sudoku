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
