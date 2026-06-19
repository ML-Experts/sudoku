import {
  toUc18BoardFileKey,
} from "./uc18BoardFile";

export function toUc18BoardImageRequestKey(boardFile: {
  preparationName: string;
  sourceName: string;
  boardFolderName: string;
}): string {
  return toUc18BoardFileKey({
    preparationName: boardFile.preparationName,
    sourceName: boardFile.sourceName,
    boardFolderName: boardFile.boardFolderName,
  });
}
