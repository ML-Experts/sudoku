import type { Uc19BoardSourceDraft, Uc19BoardSourceSplit } from "../domain/uc19BoardSourceDraft";
import type { Uc19BoardSourceDraftValidation } from "../domain/validateUc19BoardSourceDraft";

export type Uc19BoardFoldersSelectionStatus = "idle" | "loading" | "success" | "error";

export type Uc19BoardFoldersSelectionState = {
  status: Uc19BoardFoldersSelectionStatus;
  preparationName: string | null;
  drafts: Uc19BoardSourceDraft[];
  totalCount: number;
  error: string | null;
  errorType: string | null;
  httpStatus: number | null;
};

export type Uc19BoardFoldersSelectionAction =
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
      drafts: Uc19BoardSourceDraft[];
      totalCount: number;
    }
  | {
      type: "loadFailed";
      preparationName: string;
      error: string;
      errorType: string | null;
      httpStatus: number | null;
      clearDrafts: boolean;
    }
  | {
      type: "sourceEnabledToggled";
      folderName: string;
    }
  | {
      type: "sourceSplitsUpdated";
      folderName: string;
      splits: Uc19BoardSourceSplit[];
    };

export type UseUc19BoardFoldersSelectionOptions = {
  apiBaseUrl: string;
  preparationName: string | null;
  accessToken?: string | null;
  onUnauthorized?: () => void;
};

export type UseUc19BoardFoldersSelectionResult = {
  status: Uc19BoardFoldersSelectionStatus;
  preparationName: string | null;
  drafts: Uc19BoardSourceDraft[];
  selectedDrafts: Uc19BoardSourceDraft[];
  selectedCount: number;
  invalidSelectedCount: number;
  totalCount: number;
  error: string | null;
  errorType: string | null;
  httpStatus: number | null;
  validationByKey: Record<string, Uc19BoardSourceDraftValidation>;
  loadBoardFolders: (preparationName: string) => Promise<void>;
  retryLoadBoardFolders: () => Promise<void>;
  toggleBoardSourceEnabled: (folderName: string) => void;
  toggleBoardSourceSplit: (
    folderName: string,
    split: Uc19BoardSourceSplit
  ) => void;
  updateBoardSourceSplits: (
    folderName: string,
    splits: Uc19BoardSourceSplit[]
  ) => void;
};

export const defaultUc19BoardFoldersSelectionState: Uc19BoardFoldersSelectionState =
  {
    status: "idle",
    preparationName: null,
    drafts: [],
    totalCount: 0,
    error: null,
    errorType: null,
    httpStatus: null,
  };
