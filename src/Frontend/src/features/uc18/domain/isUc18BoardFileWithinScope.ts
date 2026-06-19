import type { Uc18BoardFile } from "./uc18BoardFile";

export function isUc18BoardFileWithinScope(
  boardFile: Uc18BoardFile,
  preparationName: string,
  sourceName: string
): boolean {
  return (
    boardFile.preparationName === preparationName &&
    boardFile.sourceName === sourceName
  );
}
