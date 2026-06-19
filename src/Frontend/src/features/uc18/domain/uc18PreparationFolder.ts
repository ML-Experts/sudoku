export type Uc18PreparationFolderType = "board" | "digit";

export type Uc18PreparationFolder = {
  key: string;
  preparationName: string;
  type: Uc18PreparationFolderType;
  folderName: string;
};

export function isUc18PreparationFolderType(
  value: string
): value is Uc18PreparationFolderType {
  return value === "board" || value === "digit";
}
