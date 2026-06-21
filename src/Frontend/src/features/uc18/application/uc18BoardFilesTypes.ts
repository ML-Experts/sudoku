import type { Uc18BoardFile } from "../domain/uc18BoardFile";

export const defaultUc18BoardFilesPage = 1;
export const defaultUc18BoardFilesPageSize = 24;

export type Uc18BoardFilesStatus = "idle" | "loading" | "success" | "error";

export type Uc18BoardFilesState = {
  status: Uc18BoardFilesStatus;
  preparationName: string | null;
  sourceName: string | null;
  items: Uc18BoardFile[];
  page: number;
  pageSize: number;
  totalCount: number;
  error: string | null;
  errorType: string | null;
  httpStatus: number | null;
};

export type Uc18BoardFilesAction =
  | {
      type: "stateReset";
    }
  | {
      type: "loadStarted";
      preparationName: string;
      sourceName: string;
      page: number;
      pageSize: number;
    }
  | {
      type: "loadSucceeded";
      preparationName: string;
      sourceName: string;
      items: Uc18BoardFile[];
      page: number;
      pageSize: number;
      totalCount: number;
    }
  | {
      type: "loadFailed";
      preparationName: string;
      sourceName: string;
      page: number;
      pageSize: number;
      error: string;
      errorType: string | null;
      httpStatus: number | null;
      clearItems: boolean;
    };

export type UseUc18BoardFilesOptions = {
  apiBaseUrl: string;
  preparationName: string | null;
  sourceName: string | null;
  accessToken?: string | null;
  onUnauthorized?: () => void;
};

export type UseUc18BoardFilesResult = {
  status: Uc18BoardFilesStatus;
  preparationName: string | null;
  sourceName: string | null;
  items: Uc18BoardFile[];
  page: number;
  pageSize: number;
  totalCount: number;
  totalPages: number;
  error: string | null;
  errorType: string | null;
  httpStatus: number | null;
  canGoToPreviousPage: boolean;
  canGoToNextPage: boolean;
  loadBoardFiles: (
    preparationName: string,
    sourceName: string,
    page?: number,
    pageSize?: number
  ) => Promise<void>;
  retryLoadBoardFiles: () => Promise<void>;
  goToPage: (page: number) => Promise<void>;
  goToNextPage: () => Promise<void>;
  goToPreviousPage: () => Promise<void>;
};

export const defaultUc18BoardFilesState: Uc18BoardFilesState = {
  status: "idle",
  preparationName: null,
  sourceName: null,
  items: [],
  page: defaultUc18BoardFilesPage,
  pageSize: defaultUc18BoardFilesPageSize,
  totalCount: 0,
  error: null,
  errorType: null,
  httpStatus: null,
};
