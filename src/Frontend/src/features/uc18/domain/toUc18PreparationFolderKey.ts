import type { Uc18PreparationFolderType } from "./uc18PreparationFolder";

type Uc18PreparationFolderIdentity = {
  folderName: string;
  type: Uc18PreparationFolderType;
};

export function toUc18PreparationFolderKey({
  folderName,
  type,
}: Uc18PreparationFolderIdentity): string {
  return `${type}:${folderName}`;
}
