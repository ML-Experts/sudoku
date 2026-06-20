import type {
  Uc19PreparationSourceDraft,
  Uc19PreparationSourceSplit,
  Uc19PreparationSourceType,
} from "./uc19PreparationSourceDraft";

export type Uc19DigitSourceType = Extract<Uc19PreparationSourceType, "digit">;

export type Uc19DigitSourceSplit = Uc19PreparationSourceSplit;

export type Uc19DigitSourceDraft = Omit<Uc19PreparationSourceDraft, "type"> & {
  type: Uc19DigitSourceType;
};
