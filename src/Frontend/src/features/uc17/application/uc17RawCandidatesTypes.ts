import type { CreateDatasetPreparationSourceApiEntry } from "../../../types/api";
import type { Uc17RawCandidate } from "../domain/uc17RawCandidate";

export type Uc17RawCandidatesStatus = "idle" | "loading" | "success" | "error";

export type Uc17RawCandidatesState = {
  status: Uc17RawCandidatesStatus;
  candidates: Uc17RawCandidate[];
  selectedKeys: string[];
  error: string | null;
  errorType: string | null;
  httpStatus: number | null;
  unknownTypeCount: number;
};

export type Uc17RawCandidatesAction =
  | {
      type: "loadStarted";
    }
  | {
      type: "loadSucceeded";
      candidates: Uc17RawCandidate[];
      selectedKeys: string[];
      unknownTypeCount: number;
    }
  | {
      type: "loadFailed";
      error: string;
      errorType: string | null;
      httpStatus: number | null;
    }
  | {
      type: "selectionToggled";
      candidateKey: string;
    };

export type UseUc17RawCandidatesOptions = {
  apiBaseUrl: string;
  accessToken?: string | null;
  onUnauthorized?: () => void;
};

export type UseUc17RawCandidatesResult = {
  status: Uc17RawCandidatesStatus;
  candidates: Uc17RawCandidate[];
  selectedKeys: string[];
  selectedCount: number;
  error: string | null;
  errorType: string | null;
  httpStatus: number | null;
  unknownTypeCount: number;
  sourceDrafts: CreateDatasetPreparationSourceApiEntry[];
  loadRawCandidates: () => Promise<void>;
  retryLoadRawCandidates: () => Promise<void>;
  toggleRawCandidateSelection: (candidateKey: string) => void;
};

export const defaultUc17RawCandidatesState: Uc17RawCandidatesState = {
  status: "idle",
  candidates: [],
  selectedKeys: [],
  error: null,
  errorType: null,
  httpStatus: null,
  unknownTypeCount: 0,
};
