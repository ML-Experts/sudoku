import type { Uc14ContextState } from "./uc14ParameterFieldState";
import type { Uc14NumberParameterDefinition } from "./uc14ParameterDefinition";

export type SolveCellInferenceParameterKey =
  | "emptyCellDarkPixelRatioThreshold"
  | "emptyCellInnerMarginRatio"
  | "centerAreaRatio"
  | "minComponentAreaRatio"
  | "lineArtifactMinSpanRatio"
  | "lineArtifactMaxThicknessRatio";

export type SolveCellInferenceContextState =
  Uc14ContextState<SolveCellInferenceParameterKey>;

export const solveCellInferenceParameterDefinitions: readonly Uc14NumberParameterDefinition<SolveCellInferenceParameterKey>[] =
  [
    {
      key: "emptyCellDarkPixelRatioThreshold",
      kind: "number",
      label: "Prog ciemnych pikseli pustej komorki",
      description:
        "Maksymalny udzial ciemnych pikseli w obszarze diagnostycznym, przy ktorym komorka nadal jest traktowana jako pusta.",
      guidance: {
        purpose:
          "Steruje czuloscia heurystyki odrozniajacej pusta komorke od komorki z cyfra lub artefaktem.",
        effect:
          "Nizsza wartosc szybciej uzna komorke za niepusta. Wyzsza daje wieksza tolerancje na szum, ale moze przepuscic slabe cyfry jako puste.",
        whenToChange:
          "Warto zmienic tylko wtedy, gdy widzisz regularne pomylki: puste pola sa czytane jako cyfry albo cienkie cyfry sa gubione.",
        recommendation:
          "Zacznij od drobnych zmian o 0.01 i porownuj wynik na kilku trudniejszych planszach.",
      },
      min: 0,
      max: 1,
      minInclusive: true,
      maxInclusive: true,
      step: 0.01,
      advanced: true,
    },
    {
      key: "emptyCellInnerMarginRatio",
      kind: "number",
      label: "Margines wewnetrznego obszaru",
      description:
        "Margines wycinany od krawedzi komorki przed policzeniem ciemnych pikseli dla heurystyki pustego pola.",
      guidance: {
        purpose:
          "Pozwala ograniczyc wplyw ramek, siatki i zabrudzen przy krawedziach komorki.",
        effect:
          "Wiekszy margines mocniej ignoruje brzegi komorki. Mniejszy bierze pod uwage wiecej obrazu, ale latwiej zlapie artefakty.",
        whenToChange:
          "Ma sens glownie wtedy, gdy siatka sudoku albo cienie przy krawedziach zaburzaja wykrywanie pustych komorek.",
        recommendation:
          "Jesli nie testujesz konkretnego problemu z kadrowaniem komorki, zostaw wartosc domyslna.",
      },
      min: 0,
      max: 0.49,
      minInclusive: true,
      maxInclusive: true,
      step: 0.01,
      advanced: true,
    },
    {
      key: "centerAreaRatio",
      kind: "number",
      label: "Rozmiar centralnego obszaru",
      description:
        "Udzial szerokosci i wysokosci komorki uzywany do wyciecia centralnego kwadratu analizowanego przy decyzji pusta czy zajeta.",
      guidance: {
        purpose:
          "Ustala, jak duzy wycinek srodka komorki jest analizowany po odcieciu brzegow.",
        effect:
          "Wieksza wartosc bierze pod uwage wiecej srodka komorki. Mniejsza mocniej skupia sie na samym centrum, ale moze pominac fragment cienkiej cyfry.",
        whenToChange:
          "Warto zmienic, gdy cyfry sa czesto ucinane przez zbyt maly obszar albo gdy do analizy wpada za duzo szumu z otoczenia.",
        recommendation:
          "Najczesciej wystarcza niewielkie korekty o 0.05 wzgledem wartosci domyslnej.",
      },
      min: 0.01,
      max: 1,
      minInclusive: true,
      maxInclusive: true,
      step: 0.01,
      advanced: true,
    },
    {
      key: "minComponentAreaRatio",
      kind: "number",
      label: "Minimalny udzial pola komponentu",
      description:
        "Minimalny rozmiar skladowej foregroundu w centralnym obszarze, ponizej ktorego traktujemy ja jako drobny artefakt.",
      guidance: {
        purpose:
          "Pomaga odfiltrowac male smieci i pojedyncze piksele zanim system uzna komorke za zajeta.",
        effect:
          "Wieksza wartosc agresywniej usuwa male komponenty. Mniejsza zachowuje wiecej detali, ale moze przepuszczac szum.",
        whenToChange:
          "Przydaje sie, gdy puste komorki sa odczytywane jako zajete przez drobne zabrudzenia albo gdy cienkie cyfry sa zbyt mocno czyszczone.",
        recommendation:
          "Zmniejszaj ostroznie, jesli model zaczyna gubic cienkie fragmenty cyfr.",
      },
      min: 0,
      max: 1,
      minInclusive: true,
      maxInclusive: true,
      step: 0.005,
      advanced: true,
    },
    {
      key: "lineArtifactMinSpanRatio",
      kind: "number",
      label: "Minimalna dlugosc artefaktu liniowego",
      description:
        "Minimalna dlugosc komponentu wzgledem centralnego obszaru, od ktorej cienka linia jest traktowana jako artefakt siatki.",
      guidance: {
        purpose:
          "Pozwala wykrywac dlugie cienkie pozostalosci linii poziomych i pionowych w centrum komorki.",
        effect:
          "Wieksza wartosc usuwa tylko bardzo dlugie linie. Mniejsza latwiej uzna krotsze smugi za artefakt.",
        whenToChange:
          "Warto dostroic, gdy po binaryzacji w centrum zostaja fragmenty siatki albo gdy system usuwa pionowe i poziome kreski nalezace do cyfry.",
        recommendation:
          "Testuj razem z gruboscia artefaktu liniowego, bo te parametry dzialaja w parze.",
      },
      min: 0,
      max: 1,
      minInclusive: true,
      maxInclusive: true,
      step: 0.01,
      advanced: true,
    },
    {
      key: "lineArtifactMaxThicknessRatio",
      kind: "number",
      label: "Maksymalna grubosc artefaktu liniowego",
      description:
        "Maksymalna grubosc komponentu wzgledem centralnego obszaru, przy ktorej dlugi element nadal jest usuwany jako artefakt linii.",
      guidance: {
        purpose:
          "Ogranicza usuwanie do cienkich pozostalosci siatki i pomaga nie skasowac grubszych fragmentow cyfry.",
        effect:
          "Wieksza wartosc pozwala wycinac grubsze linie. Mniejsza jest bezpieczniejsza dla cyfr, ale moze zostawic czesc siatki.",
        whenToChange:
          "Ma sens wtedy, gdy w pustych komorkach zostaja resztki linii albo gdy cyfry z pionowymi kreskami sa nadmiernie czyszczone.",
        recommendation:
          "Zmiany rob krokami o 0.01 i sprawdzaj efekt na cyfrach 1, 4 i 7 oraz na pustych komorkach blisko siatki.",
      },
      min: 0,
      max: 1,
      minInclusive: true,
      maxInclusive: true,
      step: 0.01,
      advanced: true,
    },
  ];
