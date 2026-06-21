import type { Uc18BoardFile } from "../domain/uc18BoardFile";

export type Uc18DeleteBoardFileStatus = "idle" | "deleting" | "success" | "error";

export type Uc18DeleteBoardFileState = {
  status: Uc18DeleteBoardFileStatus;
  boardFileKey: string | null;
  boardFolderName: string | null;
  remainingItemsCount: number | null;
  error: string | null;
  errorType: string | null;
  httpStatus: number | null;
};

export type Uc18DeleteBoardFileAction =
  | {
      type: "stateReset";
    }
  | {
      type: "deleteStarted";
      boardFileKey: string;
      boardFolderName: string;
    }
  | {
      type: "deleteSucceeded";
      boardFileKey: string;
      boardFolderName: string;
      remainingItemsCount: number;
    }
  | {
      type: "deleteFailed";
      boardFileKey: string | null;
      boardFolderName: string | null;
      error: string;
      errorType: string | null;
      httpStatus: number | null;
    };

export type UseUc18DeleteBoardFileOptions = {
  apiBaseUrl: string;
  preparationName: string | null;
  sourceName: string | null;
  page: number;
  pageSize: number;
  accessToken?: string | null;
  onUnauthorized?: () => void;
  loadBoardFiles: (
    preparationName: string,
    sourceName: string,
    page?: number,
    pageSize?: number
  ) => Promise<void>;
};

export type UseUc18DeleteBoardFileResult = {
  status: Uc18DeleteBoardFileStatus;
  deletingBoardFileKey: string | null;
  boardFolderName: string | null;
  remainingItemsCount: number | null;
  error: string | null;
  errorType: string | null;
  httpStatus: number | null;
  isDeleting: boolean;
  deleteBoardFile: (boardFile: Uc18BoardFile) => Promise<boolean>;
  retryDeleteBoardFile: (boardFile: Uc18BoardFile) => Promise<boolean>;
  clearDeleteFeedback: () => void;
};

export const defaultUc18DeleteBoardFileState: Uc18DeleteBoardFileState = {
  status: "idle",
  boardFileKey: null,
  boardFolderName: null,
  remainingItemsCount: null,
  error: null,
  errorType: null,
  httpStatus: null,
};
