import type { ImageApiEntry } from "../../../types/api";

export type Uc20LocalImageDraft = {
  fileName: string;
  mimeType: string;
  sizeBytes: number;
  previewUrl: string;
  requestEntry: ImageApiEntry;
};
