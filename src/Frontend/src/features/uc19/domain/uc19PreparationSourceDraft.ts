export type Uc19PreparationSourceType = "board" | "digit";

export type Uc19PreparationSourceSplit = "mix" | "train" | "val" | "test";

export type Uc19PreparationSourceDraft = {
  key: string;
  preparationName: string;
  folderName: string;
  type: Uc19PreparationSourceType;
  enabled: boolean;
  splits: Uc19PreparationSourceSplit[];
};
