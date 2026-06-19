import type { DatasetPreparationFoldersApiResponse } from "../../../types/api";
import {
  isUc18PreparationFolderType,
  type Uc18PreparationFolder,
  type Uc18PreparationFolderType,
} from "./uc18PreparationFolder";
import { toUc18PreparationFolderKey } from "./toUc18PreparationFolderKey";

export function mapDatasetPreparationFoldersToDomain(
  response: DatasetPreparationFoldersApiResponse,
  expectedType: Uc18PreparationFolderType
): Uc18PreparationFolder[] {
  if (!isUc18PreparationFolderType(response.type)) {
    throw new Error(`Backend zwrocil nieobslugiwany typ folderow: ${response.type}.`);
  }

  if (response.type !== expectedType) {
    throw new Error(
      `Backend zwrocil typ folderow ${response.type}, ale oczekiwano ${expectedType}.`
    );
  }

  return response.items.map((folderName) => ({
    key: toUc18PreparationFolderKey({
      folderName,
      type: expectedType,
    }),
    preparationName: response.preparationName,
    type: expectedType,
    folderName,
  }));
}
