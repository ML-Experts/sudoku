const MAX_PREPARATION_NAME_LENGTH = 160;

export type PreparationRequestValidationInput = {
  preparationName: string;
  selectedCount: number;
};

export function validatePreparationRequest({
  preparationName,
  selectedCount,
}: PreparationRequestValidationInput): string | null {
  const trimmedName = preparationName.trim();

  if (!trimmedName) {
    return "Podaj nazwe przygotowania.";
  }

  if (trimmedName.length > MAX_PREPARATION_NAME_LENGTH) {
    return `Nazwa przygotowania nie moze byc dluzsza niz ${MAX_PREPARATION_NAME_LENGTH} znakow.`;
  }

  if (
    trimmedName.includes("..") ||
    /[\\/:*?"<>|\u0000-\u001F]/u.test(trimmedName)
  ) {
    return "Nazwa przygotowania zawiera niedozwolone znaki.";
  }

  if (selectedCount === 0) {
    return "Wybierz przynajmniej jedno zrodlo raw.";
  }

  return null;
}

export { MAX_PREPARATION_NAME_LENGTH };
