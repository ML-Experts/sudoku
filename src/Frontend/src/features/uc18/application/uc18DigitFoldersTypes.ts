import type { Uc18PreparationFolder } from "../domain/uc18PreparationFolder";

export type Uc18DigitFoldersStatus = "idle" | "loading" | "success" | "error";

export type Uc18DigitFoldersState = {
  status: Uc18DigitFoldersStatus;
  preparationName: string | null;
  folders: Uc18PreparationFolder[];
  totalCount: number;
  error: string | null;
  errorType: string | null;
  httpStatus: number | null;
};

export type Uc18DigitFoldersAction =
  | {
      type: "stateReset";
    }
  | {
      type: "loadStarted";
      preparationName: string;
    }
  | {
      type: "loadSucceeded";
      preparationName: string;
      folders: Uc18PreparationFolder[];
      totalCount: number;
    }
  | {
      type: "loadFailed";
      preparationName: string;
      error: string;
      errorType: string | null;
      httpStatus: number | null;
    };

export type UseUc18DigitFoldersOptions = {
  apiBaseUrl: string;
  preparationName: string | null;
  accessToken?: string | null;
  onUnauthorized?: () => void;
};

export type UseUc18DigitFoldersResult = {
  status: Uc18DigitFoldersStatus;
  preparationName: string | null;
  folders: Uc18PreparationFolder[];
  totalCount: number;
  error: string | null;
  errorType: string | null;
  httpStatus: number | null;
  loadDigitFolders: (preparationName: string) => Promise<void>;
  retryLoadDigitFolders: () => Promise<void>;
};

export const defaultUc18DigitFoldersState: Uc18DigitFoldersState = {
  status: "idle",
  preparationName: null,
  folders: [],
  totalCount: 0,
  error: null,
  errorType: null,
  httpStatus: null,
};
