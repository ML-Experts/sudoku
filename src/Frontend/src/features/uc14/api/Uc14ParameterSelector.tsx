import { useEffect, useMemo, useState, type ReactNode } from "react";

import type { Uc14ParameterDefinition } from "../domain/uc14ParameterDefinition";

export type Uc14ParameterSelectorState<TKey extends string> = Record<
  TKey,
  {
    error: string | null;
    isDirty: boolean;
  }
>;

type Uc14ParameterSelectorProps<TKey extends string> = {
  title: string;
  description: string;
  definitions: readonly Uc14ParameterDefinition<TKey>[];
  state: Uc14ParameterSelectorState<TKey>;
  children: (activeKey: TKey) => ReactNode;
};

export function Uc14ParameterSelector<TKey extends string>({
  title,
  description,
  definitions,
  state,
  children,
}: Uc14ParameterSelectorProps<TKey>) {
  const suggestedKey = useMemo(() => {
    const errorDefinition = definitions.find((definition) => state[definition.key].error);
    if (errorDefinition) {
      return errorDefinition.key;
    }

    const dirtyDefinition = definitions.find((definition) => state[definition.key].isDirty);
    if (dirtyDefinition) {
      return dirtyDefinition.key;
    }

    return definitions[0]?.key ?? null;
  }, [definitions, state]);

  const [activeKey, setActiveKey] = useState<TKey | null>(suggestedKey);

  useEffect(() => {
    setActiveKey((current) => {
      if (!current) {
        return suggestedKey;
      }

      const exists = definitions.some((definition) => definition.key === current);
      return exists ? current : suggestedKey;
    });
  }, [definitions, suggestedKey]);

  useEffect(() => {
    const errorDefinition = definitions.find((definition) => state[definition.key].error);
    if (errorDefinition && activeKey !== errorDefinition.key) {
      setActiveKey(errorDefinition.key);
    }
  }, [activeKey, definitions, state]);

  if (!activeKey) {
    return null;
  }

  return (
    <section className="uc14-selector-section">
      <div className="uc14-selector-header">
        <div>
          <h4>{title}</h4>
          <p className="muted-copy">{description}</p>
        </div>
      </div>

      <div className="uc14-selector-list" role="tablist" aria-label={title}>
        {definitions.map((definition) => {
          const fieldState = state[definition.key];
          const isActive = definition.key === activeKey;
          const buttonClassName = [
            "uc14-selector-button",
            isActive ? "is-active" : "",
            fieldState.error ? "has-error" : "",
            fieldState.isDirty ? "is-dirty" : "",
          ]
            .filter(Boolean)
            .join(" ");

          return (
            <button
              key={definition.key}
              className={buttonClassName}
              type="button"
              role="tab"
              aria-selected={isActive}
              onClick={() => setActiveKey(definition.key)}
            >
              <span className="uc14-selector-button-copy">
                <span>{definition.label}</span>
                {definition.advanced ? (
                  <span className="uc14-selector-tag">Advanced</span>
                ) : null}
              </span>
              <span className="uc14-selector-button-status">
                {fieldState.error
                  ? "Blad"
                  : fieldState.isDirty
                    ? "Override"
                    : "Domyslne"}
              </span>
            </button>
          );
        })}
      </div>

      <div className="uc14-selector-editor" role="tabpanel">
        {children(activeKey)}
      </div>
    </section>
  );
}
