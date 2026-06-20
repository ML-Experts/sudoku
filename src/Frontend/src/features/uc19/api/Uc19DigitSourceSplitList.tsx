import type {
  Uc19DigitSourceDraft,
  Uc19DigitSourceSplit,
} from "../domain/uc19DigitSourceDraft";
import type { Uc19DigitSourceDraftValidation } from "../domain/validateUc19DigitSourceDraft";

type Uc19DigitSourceSplitListProps = {
  drafts: Uc19DigitSourceDraft[];
  validationByKey: Record<string, Uc19DigitSourceDraftValidation>;
  disabled?: boolean;
  onToggleEnabled: (folderName: string) => void;
  onToggleSplit: (folderName: string, split: Uc19DigitSourceSplit) => void;
};

const splitOptions: Uc19DigitSourceSplit[] = ["mix", "train", "val", "test"];

function formatSplitsCopy(splits: Uc19DigitSourceSplit[]): string {
  if (splits.length === 0) {
    return "brak";
  }

  return splits.join(", ");
}

export function Uc19DigitSourceSplitList({
  drafts,
  validationByKey,
  disabled = false,
  onToggleEnabled,
  onToggleSplit,
}: Uc19DigitSourceSplitListProps) {
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
                Nazwa folderu trafi 1:1 do <code>sources[].name</code> jako zrodlo{" "}
                <code>digit</code> w dalszym buildzie.
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
