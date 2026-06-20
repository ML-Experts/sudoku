import type {
  Uc19BoardSourceDraft,
  Uc19BoardSourceSplit,
} from "../domain/uc19BoardSourceDraft";
import type { Uc19BoardSourceDraftValidation } from "../domain/validateUc19BoardSourceDraft";

type Uc19BoardSourceSplitListProps = {
  drafts: Uc19BoardSourceDraft[];
  validationByKey: Record<string, Uc19BoardSourceDraftValidation>;
  disabled?: boolean;
  onToggleEnabled: (folderName: string) => void;
  onToggleSplit: (folderName: string, split: Uc19BoardSourceSplit) => void;
};

const splitOptions: Uc19BoardSourceSplit[] = ["mix", "train", "val", "test"];

function formatSplitsCopy(splits: Uc19BoardSourceSplit[]): string {
  if (splits.length === 0) {
    return "brak";
  }

  return splits.join(", ");
}

export function Uc19BoardSourceSplitList({
  drafts,
  validationByKey,
  disabled = false,
  onToggleEnabled,
  onToggleSplit,
}: Uc19BoardSourceSplitListProps) {
  return (
    <ul className="uc19-source-list">
      {drafts.map((draft) => {
        const validation = validationByKey[draft.key] ?? {
          isValid: true,
          message: null,
        };
        const itemClassName = [
          "uc19-source-item",
          draft.enabled ? "is-enabled" : "is-disabled",
          !validation.isValid ? "is-invalid" : "",
        ]
          .filter(Boolean)
          .join(" ");

        return (
          <li key={draft.key} className={itemClassName}>
            <div className="uc19-source-header">
              <label className="uc19-source-toggle">
                <input
                  type="checkbox"
                  checked={draft.enabled}
                  disabled={disabled}
                  onChange={() => onToggleEnabled(draft.folderName)}
                />
                <span className="uc19-source-name">
                  <strong>{draft.folderName}</strong>
                </span>
              </label>
              <span className="uc17-stat-chip">
                Typ: <code>{draft.type}</code>
              </span>
            </div>

            <div className="uc19-source-controls">
              <p className="muted-copy">
                Nazwa folderu trafi 1:1 do <code>sources[].name</code> w dalszym buildzie.
              </p>

              <div className="uc12-splits">
                {splitOptions.map((split) => (
                  <label
                    key={`${draft.key}-${split}`}
                    className={!draft.enabled ? "uc19-split-option is-disabled" : "uc19-split-option"}
                  >
                    <input
                      type="checkbox"
                      checked={draft.splits.includes(split)}
                      disabled={disabled || !draft.enabled}
                      onChange={() => onToggleSplit(draft.folderName, split)}
                    />
                    <span>{split}</span>
                  </label>
                ))}
              </div>

              {!validation.isValid ? (
                <p className="uc19-source-validation">{validation.message}</p>
              ) : draft.enabled ? (
                <p className="muted-copy">
                  Wybrane splity: <code>{formatSplitsCopy(draft.splits)}</code>
                </p>
              ) : (
                <p className="muted-copy">
                  Wlacz zrodlo, aby przypisac splity do builda datasetu.
                </p>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
