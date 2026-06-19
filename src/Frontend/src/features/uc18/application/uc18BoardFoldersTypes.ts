import type { Uc18PreparationFolder } from "../domain/uc18PreparationFolder";

export type Uc18BoardFoldersStatus = "idle" | "loading" | "success" | "error";

export type Uc18BoardFoldersState = {
  status: Uc18BoardFoldersStatus;
  preparationName: string | null;
  folders: Uc18PreparationFolder[];
  totalCount: number;
  selectedSourceName: string | null;
  error: string | null;
  errorType: string | null;
  httpStatus: number | null;
};

export type Uc18BoardFoldersAction =
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
      selectedSourceName: string | null;
    }
  | {
      type: "loadFailed";
      preparationName: string;
      error: string;
      errorType: string | null;
      httpStatus: number | null;
      clearSelection: boolean;
    }
  | {
      type: "selectionChanged";
      sourceName: string;
    };

export type UseUc18BoardFoldersOptions = {
  apiBaseUrl: string;
  preparationName: string | null;
  accessToken?: string | null;
  onUnauthorized?: () => void;
};

export type UseUc18BoardFoldersResult = {
  status: Uc18BoardFoldersStatus;
  preparationName: string | null;
  folders: Uc18PreparationFolder[];
  selectedSourceName: string | null;
  selectedFolder: Uc18PreparationFolder | null;
  error: string | null;
  errorType: string | null;
  httpStatus: number | null;
  totalCount: number;
  loadBoardFolders: (preparationName: string) => Promise<void>;
  retryLoadBoardFolders: () => Promise<void>;
  selectBoardSource: (sourceName: string) => void;
};

export const defaultUc18BoardFoldersState: Uc18BoardFoldersState = {
  status: "idle",
  preparationName: null,
  folders: [],
  totalCount: 0,
  selectedSourceName: null,
  error: null,
  errorType: null,
  httpStatus: null,
};
