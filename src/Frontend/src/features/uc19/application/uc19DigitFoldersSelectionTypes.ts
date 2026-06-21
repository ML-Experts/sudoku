import type { Uc19DigitSourceDraft, Uc19DigitSourceSplit } from "../domain/uc19DigitSourceDraft";
import type { Uc19DigitSourceDraftValidation } from "../domain/validateUc19DigitSourceDraft";

export type Uc19DigitFoldersSelectionStatus = "idle" | "loading" | "success" | "error";

export type Uc19DigitFoldersSelectionState = {
  status: Uc19DigitFoldersSelectionStatus;
  preparationName: string | null;
  drafts: Uc19DigitSourceDraft[];
  totalCount: number;
  error: string | null;
  errorType: string | null;
  httpStatus: number | null;
};

export type Uc19DigitFoldersSelectionAction =
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
      drafts: Uc19DigitSourceDraft[];
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
      splits: Uc19DigitSourceSplit[];
    };

export type UseUc19DigitFoldersSelectionOptions = {
  apiBaseUrl: string;
  preparationName: string | null;
  accessToken?: string | null;
  onUnauthorized?: () => void;
};

export type UseUc19DigitFoldersSelectionResult = {
  status: Uc19DigitFoldersSelectionStatus;
  preparationName: string | null;
  drafts: Uc19DigitSourceDraft[];
  selectedDrafts: Uc19DigitSourceDraft[];
  selectedCount: number;
  invalidSelectedCount: number;
  totalCount: number;
  error: string | null;
  errorType: string | null;
  httpStatus: number | null;
  validationByKey: Record<string, Uc19DigitSourceDraftValidation>;
  loadDigitFolders: (preparationName: string) => Promise<void>;
  retryLoadDigitFolders: () => Promise<void>;
  toggleDigitSourceEnabled: (folderName: string) => void;
  toggleDigitSourceSplit: (
    folderName: string,
    split: Uc19DigitSourceSplit
  ) => void;
  updateDigitSourceSplits: (
    folderName: string,
    splits: Uc19DigitSourceSplit[]
  ) => void;
};

export const defaultUc19DigitFoldersSelectionState: Uc19DigitFoldersSelectionState = {
  status: "idle",
  preparationName: null,
  drafts: [],
  totalCount: 0,
  error: null,
  errorType: null,
  httpStatus: null,
};
