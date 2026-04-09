export type ExampleFileApiResponse = {
  name: string;
  contentType: string;
  sizeBytes: number;
  storedAtUtc: string;
};

export type ErrorApiResponse = {
  errorType: string;
  message: string;
};
