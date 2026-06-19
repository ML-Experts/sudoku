import type { Uc18PreparationFolder } from "./uc18PreparationFolder";

export type ReconciledSelectedPreparationFolder = {
  selectedSourceName: string | null;
  wasRemoved: boolean;
};

export function reconcileSelectedPreparationFolder(
  previousSelectedSourceName: string | null,
  folders: Uc18PreparationFolder[]
): ReconciledSelectedPreparationFolder {
  if (previousSelectedSourceName === null) {
    return {
      selectedSourceName: null,
      wasRemoved: false,
    };
  }

  const stillExists = folders.some(
    (folder) => folder.folderName === previousSelectedSourceName
  );

  if (stillExists) {
    return {
      selectedSourceName: previousSelectedSourceName,
      wasRemoved: false,
    };
  }

  return {
    selectedSourceName: null,
    wasRemoved: true,
  };
}
