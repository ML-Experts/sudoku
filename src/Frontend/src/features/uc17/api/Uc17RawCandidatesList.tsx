import type { Uc17RawCandidate } from "../domain/uc17RawCandidate";

type Uc17RawCandidatesListProps = {
  title: string;
  candidates: Uc17RawCandidate[];
  selectedKeys: string[];
  onToggle: (candidateKey: string) => void;
};

export function Uc17RawCandidatesList({
  title,
  candidates,
  selectedKeys,
  onToggle,
}: Uc17RawCandidatesListProps) {
  return (
    <article className="uc17-panel">
      <h3>{title}</h3>
      {candidates.length === 0 ? (
        <p className="muted-copy">Brak kandydatow tego typu.</p>
      ) : (
        <div className="uc17-candidates-list">
          {candidates.map((candidate) => {
            const isSelected = selectedKeys.includes(candidate.key);

            return (
              <label
                key={candidate.key}
                className={`uc17-candidate ${isSelected ? "is-selected" : ""}`}
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => onToggle(candidate.key)}
                />
                <span>
                  <strong>{candidate.name}</strong> (<code>{candidate.type}</code>)
                </span>
              </label>
            );
          })}
        </div>
      )}
    </article>
  );
}
