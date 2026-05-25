import { loadImageElement } from "./loadImageElement";

function assertImageGridShape(imageGrid: string[][]): void {
  if (!Array.isArray(imageGrid) || imageGrid.length === 0) {
    throw new Error("Siatka obrazow do zlozenia nie moze byc pusta.");
  }

  const columnCount = imageGrid[0]?.length ?? 0;
  if (columnCount === 0) {
    throw new Error("Siatka obrazow do zlozenia musi miec co najmniej jedna kolumne.");
  }

  for (const row of imageGrid) {
    if (!Array.isArray(row) || row.length !== columnCount) {
      throw new Error("Siatka obrazow do zlozenia musi byc prostokatna.");
    }
  }
}

export async function composeImageGrid(
  imageGrid: string[][],
  signal?: AbortSignal,
): Promise<string> {
  assertImageGridShape(imageGrid);

  const loadedRows = await Promise.all(
    imageGrid.map((row) =>
      Promise.all(row.map((cellSource) => loadImageElement(cellSource, signal))),
    ),
  );

  const firstImage = loadedRows[0]?.[0];
  if (!firstImage) {
    throw new Error("Brakuje obrazu referencyjnego do zlozenia planszy.");
  }

  const cellWidth = firstImage.naturalWidth || firstImage.width;
  const cellHeight = firstImage.naturalHeight || firstImage.height;

  if (cellWidth <= 0 || cellHeight <= 0) {
    throw new Error("Obrazy komorek maja niepoprawny rozmiar do zlozenia planszy.");
  }

  const rowCount = loadedRows.length;
  const columnCount = loadedRows[0].length;
  const canvas = document.createElement("canvas");
  canvas.width = columnCount * cellWidth;
  canvas.height = rowCount * cellHeight;

  const context = canvas.getContext("2d");
  if (!context) {
    throw new Error("Przegladarka nie udostepnia kontekstu 2D dla canvas.");
  }

  for (let rowIndex = 0; rowIndex < rowCount; rowIndex += 1) {
    for (let columnIndex = 0; columnIndex < columnCount; columnIndex += 1) {
      context.drawImage(
        loadedRows[rowIndex][columnIndex],
        columnIndex * cellWidth,
        rowIndex * cellHeight,
        cellWidth,
        cellHeight,
      );
    }
  }

  return canvas.toDataURL("image/png");
}
