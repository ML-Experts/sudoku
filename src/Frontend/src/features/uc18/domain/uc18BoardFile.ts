export type Uc18BoardFile = {
  key: string;
  preparationName: string;
  sourceName: string;
  boardFolderName: string;
  imageEndpoint: string;
};

export function toUc18BoardFileKey(input: {
  preparationName: string;
  sourceName: string;
  boardFolderName: string;
}): string {
  return `${input.preparationName}:${input.sourceName}:${input.boardFolderName}`;
}
