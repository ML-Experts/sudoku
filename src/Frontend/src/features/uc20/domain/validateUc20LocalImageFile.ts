const ALLOWED_LOCAL_IMAGE_MIME_TYPES = [
  "image/jpeg",
  "image/jpg",
  "image/png",
] as const;

export const UC20_LOCAL_IMAGE_INPUT_ACCEPT =
  "image/jpeg,image/png,.jpg,.jpeg,.png";
export const MAX_LOCAL_IMAGE_SIZE_BYTES = 10 * 1024 * 1024;

export function validateUc20LocalImageFile(file: File | null): string | null {
  if (!file) {
    return "Wybierz plik obrazu Sudoku.";
  }

  if (!ALLOWED_LOCAL_IMAGE_MIME_TYPES.includes(file.type as (typeof ALLOWED_LOCAL_IMAGE_MIME_TYPES)[number])) {
    return "Dozwolone sa tylko wspierane typy obrazow: JPG, JPEG lub PNG.";
  }

  if (file.size > MAX_LOCAL_IMAGE_SIZE_BYTES) {
    return `Plik jest zbyt duzy. Maksymalny rozmiar to ${MAX_LOCAL_IMAGE_SIZE_BYTES / (1024 * 1024)} MB.`;
  }

  return null;
}

export { ALLOWED_LOCAL_IMAGE_MIME_TYPES };
