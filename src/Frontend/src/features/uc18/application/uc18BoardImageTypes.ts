export type Uc18BoardImageStatus = "idle" | "loading" | "success" | "error";

export type Uc18BoardImageState = {
  status: Uc18BoardImageStatus;
  requestKey: string | null;
  imageDataUrl: string | null;
  error: string | null;
  errorType: string | null;
  httpStatus: number | null;
};

export type Uc18BoardImageAction =
  | {
      type: "stateReset";
    }
  | {
      type: "loadStarted";
      requestKey: string;
    }
  | {
      type: "loadSucceeded";
      requestKey: string;
      imageDataUrl: string;
    }
  | {
      type: "loadFailed";
      requestKey: string;
      error: string;
      errorType: string | null;
      httpStatus: number | null;
    };

export type UseUc18BoardImageOptions = {
  apiBaseUrl: string;
  imageEndpoint: string;
  preparationName: string;
  sourceName: string;
  boardFolderName: string;
  accessToken?: string | null;
  onUnauthorized?: () => void;
};

export type UseUc18BoardImageResult = {
  status: Uc18BoardImageStatus;
  requestKey: string | null;
  imageDataUrl: string | null;
  error: string | null;
  errorType: string | null;
  httpStatus: number | null;
  loadBoardImage: () => Promise<void>;
  retryLoadBoardImage: () => Promise<void>;
};

export const defaultUc18BoardImageState: Uc18BoardImageState = {
  status: "idle",
  requestKey: null,
  imageDataUrl: null,
  error: null,
  errorType: null,
  httpStatus: null,
};
