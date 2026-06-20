import type { CellsStageState, ImageStageState } from "../../../app/state";
import {
  defaultCellsStageState,
  defaultImageStageState,
} from "../../../app/state";
import type { Uc20LocalImageDraft } from "../domain/uc20LocalImageDraft";

export type Uc20LocalImageDraftState = {
  selectedDraft: Uc20LocalImageDraft | null;
  validationError: string | null;
  isReading: boolean;
};

export const defaultUc20LocalImageDraftState: Uc20LocalImageDraftState = {
  selectedDraft: null,
  validationError: null,
  isReading: false,
};

export const defaultUc20BoardStageState: ImageStageState = {
  ...defaultImageStageState,
};

export const defaultUc20CellsStageState: CellsStageState = {
  ...defaultCellsStageState,
};
