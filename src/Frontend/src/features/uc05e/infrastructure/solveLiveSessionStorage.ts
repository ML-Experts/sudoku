import { isRecognizedGrid } from "../../uc05a/domain/recognizedGrid";
import type { PersistedLiveSolveContext } from "../application/solveLiveTypes";

const STORAGE_KEY = "sudoku.uc05.liveSolveContext";

export class PersistedLiveSolveContextStorageError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PersistedLiveSolveContextStorageError";
  }
}

function getStorage(): Storage | null {
  if (typeof window === "undefined") {
    return null;
  }

  return window.sessionStorage;
}

export function savePersistedLiveSolveContext(
  context: PersistedLiveSolveContext,
): void {
  const storage = getStorage();
  if (!storage) {
    return;
  }

  storage.setItem(STORAGE_KEY, JSON.stringify(context));
}

export function loadPersistedLiveSolveContext(): PersistedLiveSolveContext | null {
  const storage = getStorage();
  if (!storage) {
    return null;
  }

  const rawValue = storage.getItem(STORAGE_KEY);
  if (!rawValue) {
    return null;
  }

  let parsedValue: unknown;
  try {
    parsedValue = JSON.parse(rawValue) as unknown;
  } catch {
    throw new PersistedLiveSolveContextStorageError(
      "sessionStorage zawiera uszkodzony kontekst live solve.",
    );
  }

  if (!parsedValue || typeof parsedValue !== "object") {
    throw new PersistedLiveSolveContextStorageError(
      "sessionStorage zawiera niepoprawny ksztalt kontekstu live solve.",
    );
  }

  const record = parsedValue as Record<string, unknown>;
  if (
    typeof record.solveSessionId !== "string" ||
    typeof record.progressChannelUrl !== "string" ||
    !(typeof record.startedGridSignature === "string" ||
      record.startedGridSignature === null) ||
    !isRecognizedGrid(record.inputGrid)
  ) {
    throw new PersistedLiveSolveContextStorageError(
      "sessionStorage zawiera niepoprawny payload kontekstu live solve.",
    );
  }

  return {
    solveSessionId: record.solveSessionId,
    progressChannelUrl: record.progressChannelUrl,
    startedGridSignature: record.startedGridSignature,
    inputGrid: record.inputGrid,
  };
}

export function clearPersistedLiveSolveContext(): void {
  const storage = getStorage();
  if (!storage) {
    return;
  }

  storage.removeItem(STORAGE_KEY);
}
