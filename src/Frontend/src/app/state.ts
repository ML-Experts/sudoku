import type {
  CellsGridApiResponse,
  ExampleFileApiResponse,
  ExamplesListApiResponse,
  ImageApiResponse,
} from "../types/api";

export type PingResponse = {
  backendStatus: string;
  mlStatus: string;
  timestampUtc: string;
  message: string;
};

export type PingState =
  | {
      kind: "idle";
      response: null;
      error: null;
      httpStatus: null;
    }
  | {
      kind: "loading";
      response: null;
      error: null;
      httpStatus: null;
    }
  | {
      kind: "success";
      response: PingResponse;
      error: null;
      httpStatus: number;
    }
  | {
      kind: "error";
      response: PingResponse | null;
      error: string;
      httpStatus: number | null;
    };

export type UploadState =
  | {
      kind: "idle";
      error: null;
      httpStatus: null;
    }
  | {
      kind: "loading";
      error: null;
      httpStatus: null;
    }
  | {
      kind: "success";
      error: null;
      httpStatus: number;
      response: ExampleFileApiResponse;
    }
  | {
      kind: "error";
      error: string;
      httpStatus: number | null;
      errorType: string | null;
    };

export type ExamplesListState =
  | {
      kind: "idle";
      data: null;
      error: null;
      httpStatus: null;
      errorType: null;
    }
  | {
      kind: "loading";
      data: ExamplesListApiResponse | null;
      error: null;
      httpStatus: null;
      errorType: null;
    }
  | {
      kind: "success";
      data: ExamplesListApiResponse;
      error: null;
      httpStatus: number;
      errorType: null;
    }
  | {
      kind: "error";
      data: ExamplesListApiResponse | null;
      error: string;
      httpStatus: number | null;
      errorType: string | null;
    };

export type ImageStageState =
  | {
      kind: "idle";
      image: null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "loading";
      image: null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "success";
      image: ImageApiResponse;
      error: null;
      errorType: null;
      httpStatus: number;
    }
  | {
      kind: "error";
      image: null;
      error: string;
      errorType: string | null;
      httpStatus: number | null;
    };

export type CellsStageState =
  | {
      kind: "idle";
      cells: null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "loading";
      cells: null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "success";
      cells: CellsGridApiResponse;
      error: null;
      errorType: null;
      httpStatus: number;
    }
  | {
      kind: "error";
      cells: null;
      error: string;
      errorType: string | null;
      httpStatus: number | null;
    };

export type LoginState =
  | {
      kind: "idle";
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "loading";
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "error";
      error: string;
      errorType: string | null;
      httpStatus: number | null;
    };

export const defaultPingState: PingState = {
  kind: "idle",
  response: null,
  error: null,
  httpStatus: null,
};

export const defaultUploadState: UploadState = {
  kind: "idle",
  error: null,
  httpStatus: null,
};

export const defaultExamplesListState: ExamplesListState = {
  kind: "idle",
  data: null,
  error: null,
  httpStatus: null,
  errorType: null,
};

export const defaultImageStageState: ImageStageState = {
  kind: "idle",
  image: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

export const defaultCellsStageState: CellsStageState = {
  kind: "idle",
  cells: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

export const defaultLoginState: LoginState = {
  kind: "idle",
  error: null,
  errorType: null,
  httpStatus: null,
};

export type AppView = "health" | "examples" | "datasets";
export type DatasetsStep = "uc11" | "uc17" | "uc12" | "uc06" | "uc08";
