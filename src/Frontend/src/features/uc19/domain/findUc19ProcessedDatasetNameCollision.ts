import type { ProcessedDatasetListItemApiResponse } from "../../../types/api";

export function findUc19ProcessedDatasetNameCollision(
  datasetName: string,
  items: ProcessedDatasetListItemApiResponse[]
): ProcessedDatasetListItemApiResponse | null {
  const normalizedName = datasetName.trim();

  if (!normalizedName) {
    return null;
  }

  const normalizedFileName = `${normalizedName}.npz`;

  return (
    items.find(
      (item) => item.name === normalizedName || item.fileName === normalizedFileName
    ) ?? null
  );
}
