import type { Uc14ContextState } from "./uc14ParameterFieldState";
import type { Uc14NumberParameterDefinition } from "./uc14ParameterDefinition";

export type SolveLiveParameterKey = "solverStepDelayMs";

export type SolveLiveContextState = Uc14ContextState<SolveLiveParameterKey>;

export const solveLiveParameterDefinitions: readonly Uc14NumberParameterDefinition<SolveLiveParameterKey>[] =
  [
    {
      key: "solverStepDelayMs",
      kind: "number",
      label: "Opoznienie kroku solvera",
      description:
        "Sztuczne opoznienie miedzy kolejnymi krokami live solve. Wplywa tylko na nowo uruchamiana sesje.",
      guidance: {
        purpose:
          "Steruje tempem, w jakim backend publikuje kolejne snapshoty backtrackingu podczas live solve.",
        effect:
          "Nizsza wartosc przyspiesza pokaz. Wyzsza spowalnia przebieg i ulatwia sledzenie pojedynczych wpisan oraz cofniec.",
        whenToChange:
          "Zmien, gdy chcesz lepiej pokazac dzialanie solvera albo odwrotnie: przyspieszyc demo bez zmiany finalnego wyniku.",
        recommendation:
          "To parametr czysto prezentacyjny. Nie zmienia poprawnosci rozwiazania, tylko jego tempo.",
      },
      min: 0,
      max: 2000,
      minInclusive: true,
      maxInclusive: true,
      step: 1,
      unitLabel: "ms",
      integerOnly: true,
    },
  ];
