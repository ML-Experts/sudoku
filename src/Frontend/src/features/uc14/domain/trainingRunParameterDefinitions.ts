import type { Uc14ParameterDefinition } from "./uc14ParameterDefinition";

export type TrainingRunParameterKey =
  | "epochs"
  | "learningRate"
  | "batchSize"
  | "earlyStoppingPatience"
  | "lrSchedulerPatience"
  | "lrSchedulerFactor"
  | "fineTuningPolicy"
  | "useBestCheckpoint";

export const trainingRunParameterDefinitions: readonly Uc14ParameterDefinition<TrainingRunParameterKey>[] =
  [
    {
      key: "epochs",
      kind: "number",
      label: "Liczba epok",
      description:
        "Maksymalna liczba pelnych przejsc przez dane treningowe dla nowego runu.",
      guidance: {
        purpose:
          "Ustala gorny limit czasu uczenia i liczby iteracji, jakie model moze wykonac przed zatrzymaniem.",
        effect:
          "Wieksza wartosc daje modelowi wiecej szans na poprawe, ale wydluza trening i moze zwiekszyc ryzyko przeuczenia. Mniejsza skraca run, ale moze zatrzymac nauke zbyt wczesnie.",
        whenToChange:
          "Zwiekzaj, gdy model nadal poprawia metryki pod koniec runu. Zmniejszaj, gdy trening trwa za dlugo albo i tak konczy sie wczesniej przez early stopping.",
        recommendation:
          "Jesli nie masz konkretnej hipotezy eksperymentalnej, zaczynaj od wartosci domyslnej i obserwuj, ile epok faktycznie zostalo wykonanych.",
      },
      min: 1,
      minInclusive: true,
      step: 1,
      integerOnly: true,
    },
    {
      key: "learningRate",
      kind: "number",
      label: "Learning rate",
      description:
        "Tempo aktualizacji wag modelu podczas optymalizacji.",
      guidance: {
        purpose:
          "Steruje wielkoscia kroku optymalizatora przy kazdej aktualizacji parametrow modelu.",
        effect:
          "Wyzsza wartosc przyspiesza uczenie, ale moze rozchwia trening. Nizsza jest bezpieczniejsza i stabilniejsza, lecz spowalnia dochodzenie do dobrego minimum.",
        whenToChange:
          "Zmniejszaj, gdy loss skacze albo trening jest niestabilny. Zwiekzaj ostroznie, gdy uczenie idzie bardzo wolno i metryki prawie sie nie ruszaja.",
        recommendation:
          "To jeden z najbardziej czulych parametrow. Zmieniaj go malymi krokami, zwykle o rzad wielkosci albo 2-3x.",
      },
      min: 0,
      max: 1,
      minInclusive: false,
      maxInclusive: true,
      step: 0.0001,
    },
    {
      key: "useBestCheckpoint",
      kind: "select",
      label: "Najlepszy checkpoint",
      description:
        "Decyduje, czy finalny artefakt modelu ma powstac z najlepszego checkpointu walidacyjnego, czy z ostatniej wykonanej epoki.",
      guidance: {
        purpose:
          "Pozwala sterowac tym, z ktorego momentu treningu zostana wziete finalne wagi modelu wynikowego.",
        effect:
          "Opcja wlaczona preferuje checkpoint z najlepsza metryka monitorowana podczas walidacji. Opcja wylaczona zachowuje stan modelu z konca ostatniej wykonanej epoki.",
        whenToChange:
          "Wylacz, gdy chcesz swiadomie analizowac wynik koncowej epoki albo porownac zachowanie runnera bez wyboru najlepszego checkpointu. Zostaw wlaczone, gdy zalezy Ci na bezpieczniejszym wyborze finalnego modelu.",
        recommendation:
          "Dla standardowego treningu trzymaj te opcje wlaczona. Wylaczaj ja glownie do celowych eksperymentow i porownan.",
      },
      options: [
        {
          value: "true",
          label: "tak",
          description:
            "Finalny model powstaje z najlepszego checkpointu walidacyjnego. To domyslne i rekomendowane zachowanie.",
        },
        {
          value: "false",
          label: "nie",
          description:
            "Finalny model zachowuje stan z ostatniej wykonanej epoki, nawet jesli wczesniejszy checkpoint byl lepszy.",
        },
      ],
    },
    {
      key: "batchSize",
      kind: "number",
      label: "Batch size",
      description:
        "Liczba probek przetwarzanych jednoczesnie w pojedynczym kroku treningowym.",
      guidance: {
        purpose:
          "Ustala, ile danych trafia naraz do modelu przed obliczeniem gradientu i aktualizacja wag.",
        effect:
          "Wiekszy batch zwykle stabilizuje estymacje gradientu i moze przyspieszyc trening, ale zuzywa wiecej pamieci. Mniejszy batch jest lzejszy obliczeniowo, ale wprowadza wiecej szumu do uczenia.",
        whenToChange:
          "Zmniejszaj przy problemach z pamiecia albo gdy chcesz trenowac ostrozniej. Zwiekzaj, gdy masz zapas zasobow i chcesz sprawdzic bardziej stabilny przebieg.",
        recommendation:
          "Zmieniaj rozmiar batcha raczej w krokach 2x, np. 16 -> 32 -> 64.",
      },
      min: 1,
      minInclusive: true,
      step: 1,
      integerOnly: true,
    },
    {
      key: "earlyStoppingPatience",
      kind: "number",
      label: "Early stopping patience",
      description:
        "Liczba kolejnych epok bez poprawy, po ktorej trening moze zostac zakonczony przed czasem.",
      guidance: {
        purpose:
          "Chroni przed niepotrzebnym dalszym uczeniem, gdy model przestaje sie poprawiac.",
        effect:
          "Nizsza wartosc szybciej konczy run przy braku poprawy. Wyzsza daje modelowi wiecej czasu na odbicie po chwilowym pogorszeniu.",
        whenToChange:
          "Zwiekzaj, gdy walidacja poprawia sie nierowno i potrzebujesz wiecej cierpliwosci. Zmniejszaj, gdy runy zbyt dlugo miela bez realnych korzysci.",
        recommendation:
          "Dobieraj ten parametr razem z liczba epok, bo razem decyduja o realnej dlugosci treningu.",
      },
      min: 1,
      minInclusive: true,
      step: 1,
      integerOnly: true,
      advanced: true,
    },
    {
      key: "lrSchedulerPatience",
      kind: "number",
      label: "LR scheduler patience",
      description:
        "Liczba epok bez poprawy, po ktorej scheduler obniza learning rate.",
      guidance: {
        purpose:
          "Pozwala zmniejszyc tempo uczenia dopiero wtedy, gdy model utknie na platou.",
        effect:
          "Nizsza wartosc szybciej uruchamia redukcje learning rate. Wyzsza dluzej utrzymuje aktualne tempo, dajac modelowi wiecej czasu na poprawe bez interwencji schedulera.",
        whenToChange:
          "Zmniejszaj, gdy widzisz szybkie wypalenie postepu. Zwiekzaj, gdy scheduler obcina learning rate zbyt agresywnie i za szybko spowalnia run.",
        recommendation:
          "Patrz na ten parametr razem z `lrSchedulerFactor`, bo scheduler dziala sensownie dopiero jako para.",
      },
      min: 1,
      minInclusive: true,
      step: 1,
      integerOnly: true,
      advanced: true,
    },
    {
      key: "lrSchedulerFactor",
      kind: "number",
      label: "LR scheduler factor",
      description:
        "Wspolczynnik, przez ktory scheduler mnozy learning rate przy redukcji.",
      guidance: {
        purpose:
          "Okresla, jak mocno zmaleje learning rate po aktywacji schedulera.",
        effect:
          "Nizsza wartosc oznacza bardziej agresywne ciecie learning rate. Wyzsza zmniejsza go lagodniej, wiec model dluzej uczy sie w podobnym tempie.",
        whenToChange:
          "Zmniejszaj, gdy po platou model nie potrafi wejsc w stabilniejsza faze uczenia. Zwiekzaj, gdy redukcja jest zbyt mocna i trening za szybko zamiera.",
        recommendation:
          "Najczesciej sensowne sa niewielkie roznice, np. 0.5 kontra 0.3, a nie skrajne przestawienia.",
      },
      min: 0,
      max: 1,
      minInclusive: false,
      maxInclusive: false,
      step: 0.1,
      advanced: true,
    },
    {
      key: "fineTuningPolicy",
      kind: "select",
      label: "Polityka fine-tuningu",
      description:
        "Zakres warstw modelu, ktore beda aktualizowane w trakcie treningu.",
      guidance: {
        purpose:
          "Pozwala zdecydowac, czy dostrajasz caly model, czy tylko jego czesc odpowiedzialna za finalna klasyfikacje.",
        effect:
          "Opcja `all` daje najwieksza elastycznosc i moze lepiej dopasowac model do danych. `Head only` jest ostrozniejsza, zwykle szybsza i mniej ryzykowna dla juz sensownych wag bazowych.",
        whenToChange:
          "Uzyj `head-only`, gdy chcesz delikatnego dostrojenia modelu bazowego albo masz malo danych. Wybierz `all`, gdy potrzebujesz pelniejszej adaptacji do nowego zbioru.",
        recommendation:
          "Jesli nie masz jeszcze intuicji dla danego modelu, zacznij od `all`, a `head-only` traktuj jako bardziej zachowawczy wariant eksperymentu.",
      },
      advanced: true,
      options: [
        {
          value: "all",
          label: "all",
          description:
            "Aktualizuje wszystkie trenowalne warstwy modelu. To najsilniejsze dostrajanie i najlepszy wybor, gdy chcesz pelnej adaptacji.",
        },
        {
          value: "head-only",
          label: "head-only",
          description:
            "Aktualizuje tylko glowice klasyfikacyjna. To bardziej zachowawcze podejscie, dobre dla szybkich eksperymentow i mocnych modeli bazowych.",
        },
      ],
    },
  ];
