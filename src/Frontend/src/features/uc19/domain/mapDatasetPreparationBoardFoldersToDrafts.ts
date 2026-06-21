import type { DatasetPreparationFoldersApiResponse } from "../../../types/api";
import type { Uc19BoardSourceDraft } from "./uc19BoardSourceDraft";

export function mapDatasetPreparationBoardFoldersToDrafts(
  response: DatasetPreparationFoldersApiResponse
): Uc19BoardSourceDraft[] {
  if (response.type !== "board") {
    throw new Error(
      `Backend zwrocil typ folderow ${response.type}, ale oczekiwano board.`
    );
  }

  return response.items.map((folderName) => ({
    key: `board:${folderName}`,
    preparationName: response.preparationName,
    folderName,
    type: "board",
    enabled: false,
    splits: [],
  }));
}
