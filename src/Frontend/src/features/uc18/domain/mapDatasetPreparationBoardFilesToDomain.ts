import type { DatasetPreparationBoardFilesApiResponse } from "../../../types/api";
import { toUc18BoardFileKey, type Uc18BoardFile } from "./uc18BoardFile";

export function mapDatasetPreparationBoardFilesToDomain(
  response: DatasetPreparationBoardFilesApiResponse,
  expectedPreparationName: string,
  expectedSourceName: string
): Uc18BoardFile[] {
  if (response.preparationName !== expectedPreparationName) {
    throw new Error(
      `Backend zwrocil preparationName ${response.preparationName}, ale oczekiwano ${expectedPreparationName}.`
    );
  }

  if (response.sourceName !== expectedSourceName) {
    throw new Error(
      `Backend zwrocil sourceName ${response.sourceName}, ale oczekiwano ${expectedSourceName}.`
    );
  }

  return response.items.map((item) => ({
    key: toUc18BoardFileKey({
      preparationName: response.preparationName,
      sourceName: response.sourceName,
      boardFolderName: item.boardFolderName,
    }),
    preparationName: response.preparationName,
    sourceName: response.sourceName,
    boardFolderName: item.boardFolderName,
    imageEndpoint: item.imageEndpoint,
  }));
}
