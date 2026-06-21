import type { DatasetPreparationFoldersApiResponse } from "../../../types/api";
import type { Uc19DigitSourceDraft } from "./uc19DigitSourceDraft";

export function mapDatasetPreparationDigitFoldersToDrafts(
  response: DatasetPreparationFoldersApiResponse
): Uc19DigitSourceDraft[] {
  if (response.type !== "digit") {
    throw new Error(
      `Backend zwrocil typ folderow ${response.type}, ale oczekiwano digit.`
    );
  }

  return response.items.map((folderName) => ({
    key: `digit:${folderName}`,
    preparationName: response.preparationName,
    folderName,
    type: "digit",
    enabled: false,
    splits: [],
  }));
}
