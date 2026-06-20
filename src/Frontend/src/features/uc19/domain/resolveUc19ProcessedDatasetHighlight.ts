import type { ProcessedDatasetListItemApiResponse } from "../../../types/api";

export type Uc19ProcessedDatasetHighlightedItem = ProcessedDatasetListItemApiResponse & {
  isFreshlyCreated: boolean;
  isMatchingTypedName: boolean;
};

export function resolveUc19ProcessedDatasetHighlight(
  items: ProcessedDatasetListItemApiResponse[],
  createdDatasetName: string | null,
  typedDatasetName: string
): Uc19ProcessedDatasetHighlightedItem[] {
  const normalizedTypedDatasetName = typedDatasetName.trim();
  const normalizedCreatedDatasetName = createdDatasetName?.trim() ?? "";

  return items.map((item) => ({
    ...item,
    isFreshlyCreated:
      normalizedCreatedDatasetName.length > 0 && item.name === normalizedCreatedDatasetName,
    isMatchingTypedName:
      normalizedTypedDatasetName.length > 0 && item.name === normalizedTypedDatasetName,
  }));
}
