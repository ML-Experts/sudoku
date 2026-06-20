import type { SelectedPreparedDatasetSourceApiEntry } from "../../../types/api";
import type { Uc19BoardSourceDraft } from "./uc19BoardSourceDraft";
import type { Uc19DigitSourceDraft } from "./uc19DigitSourceDraft";

export function mapUc19SourceDraftsToProcessedDatasetSources(
  boardDrafts: Uc19BoardSourceDraft[],
  digitDrafts: Uc19DigitSourceDraft[],
): SelectedPreparedDatasetSourceApiEntry[] {
  const mappedBoardSources = boardDrafts
    .filter((draft) => draft.enabled)
    .map<SelectedPreparedDatasetSourceApiEntry>((draft) => ({
      name: draft.folderName,
      type: draft.type,
      splits: [...draft.splits],
    }));

  const mappedDigitSources = digitDrafts
    .filter((draft) => draft.enabled)
    .map<SelectedPreparedDatasetSourceApiEntry>((draft) => ({
      name: draft.folderName,
      type: draft.type,
      splits: [...draft.splits],
    }));

  return [...mappedBoardSources, ...mappedDigitSources];
}
