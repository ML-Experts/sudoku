import type { ImageApiResponse } from "../../types/api";

export function toImageDataUrl(image: ImageApiResponse): string {
  return `data:${image.mimeType};base64,${image.base64}`;
}
