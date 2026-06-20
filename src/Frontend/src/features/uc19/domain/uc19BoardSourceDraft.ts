import type {
  Uc19PreparationSourceDraft,
  Uc19PreparationSourceSplit,
  Uc19PreparationSourceType,
} from "./uc19PreparationSourceDraft";

export type Uc19BoardSourceType = Extract<Uc19PreparationSourceType, "board">;

export type Uc19BoardSourceSplit = Uc19PreparationSourceSplit;

export type Uc19BoardSourceDraft = Omit<Uc19PreparationSourceDraft, "type"> & {
  type: Uc19BoardSourceType;
};
