import type { Uc18PreparationFolder } from "../domain/uc18PreparationFolder";

type Uc18PreparationFoldersListBaseProps = {
  folders: Uc18PreparationFolder[];
  emptyMessage?: string;
};

type Uc18SelectablePreparationFoldersListProps =
  Uc18PreparationFoldersListBaseProps & {
    mode: "selectable";
    selectedSourceName: string | null;
    onSelect: (sourceName: string) => void;
    disabled?: boolean;
  };

type Uc18ReadonlyPreparationFoldersListProps =
  Uc18PreparationFoldersListBaseProps & {
    mode: "readonly";
    itemHint?: string;
  };

type Uc18PreparationFoldersListProps =
  | Uc18SelectablePreparationFoldersListProps
  | Uc18ReadonlyPreparationFoldersListProps;

type Uc18PreparationFolderCardProps = {
  folder: Uc18PreparationFolder;
  hint: string;
};

function Uc18PreparationFolderCard({ folder, hint }: Uc18PreparationFolderCardProps) {
  return (
    <div className="uc18-folder-card is-readonly">
      <span>
        <strong>{folder.folderName}</strong>
      </span>
      <span className="muted-copy">{hint}</span>
    </div>
  );
}

export function Uc18PreparationFoldersList({
  folders,
  emptyMessage = "Brak zrodel dla wybranego przygotowania.",
  ...props
}: Uc18PreparationFoldersListProps) {
  if (folders.length === 0) {
    return <p className="muted-copy">{emptyMessage}</p>;
  }

  if (props.mode === "readonly") {
    const itemHint = props.itemHint ?? "Widok tylko do odczytu.";

    return (
      <ul className="uc18-folders-list">
        {folders.map((folder) => (
          <li key={folder.key}>
            <Uc18PreparationFolderCard folder={folder} hint={itemHint} />
          </li>
        ))}
      </ul>
    );
  }

  const { disabled = false, selectedSourceName, onSelect } = props;

  return (
    <ul className="uc18-folders-list">
      {folders.map((folder) => {
        const isSelected = selectedSourceName === folder.folderName;

        return (
          <li key={folder.key}>
            <button
              className={`uc18-folder-button ${isSelected ? "is-active" : ""}`}
              type="button"
              onClick={() => onSelect(folder.folderName)}
              aria-pressed={isSelected}
              disabled={disabled}
            >
              <span>
                <strong>{folder.folderName}</strong>
              </span>
              <span className="muted-copy">
                {isSelected ? "Wybrane zrodlo do dalszego przegladu" : "Wybierz zrodlo"}
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
