import type {
  Uc19PreparationSourceDraft,
  Uc19PreparationSourceSplit,
} from "./uc19PreparationSourceDraft";

export type ReconciledUc19PreparationSourceDrafts<
  TDraft extends Pick<Uc19PreparationSourceDraft, "folderName" | "enabled" | "splits">,
> = {
  drafts: TDraft[];
  removedDrafts: string[];
};

export function reconcileUc19PreparationSourceDrafts<
  TDraft extends Pick<Uc19PreparationSourceDraft, "folderName" | "enabled" | "splits">,
>(
  previousDrafts: TDraft[],
  freshDrafts: TDraft[]
): ReconciledUc19PreparationSourceDrafts<TDraft> {
  const previousDraftsByFolderName = new Map(
    previousDrafts.map((draft) => [draft.folderName, draft] as const)
  );
  const freshDraftFolderNames = new Set(
    freshDrafts.map((draft) => draft.folderName)
  );
  const drafts = freshDrafts.map((freshDraft) => {
    const previousDraft = previousDraftsByFolderName.get(freshDraft.folderName);

    if (!previousDraft) {
      return freshDraft;
    }

    return {
      ...freshDraft,
      enabled: previousDraft.enabled,
      splits: [...previousDraft.splits] as Uc19PreparationSourceSplit[],
    };
  });
  const removedDrafts = previousDrafts
    .filter(
      (previousDraft) =>
        previousDraft.enabled &&
        !freshDraftFolderNames.has(previousDraft.folderName)
    )
    .map((draft) => draft.folderName);

  return {
    drafts,
    removedDrafts,
  };
}
