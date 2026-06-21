# UC-16 Refactor ML — Uspójnienie pipeline'u board i preprocessingu komórek względem draft

## Cel
- Jako zespół chcemy ujednolicić usługi `MachineLearning/infrastructure` odpowiedzialne za budowę `board` oraz przygotowanie komórek do datasetu, treningu i ewaluacji, tak aby ich wynik był zgodny z kierunkiem wypracowanym eksperymentalnie w `src/MachineLearning/draft`.
- Celem refaktoru nie jest rozwijanie eksperymentu w `draft`, tylko przeniesienie sprawdzonej logiki do właściwych usług produkcyjnych `infrastructure`.
- Efekt końcowy ma być wizualnie i semantycznie spójny z założeniami `PRD`, `UC-04`, `UC-06`, `UC-12` i istniejącym workflow `UC-16`.

## Endpoint i punkt wejścia
- Ta historyjka dotyczy istniejącego wewnętrznego endpointu `BE -> ML`:
  - `POST /ml/datasets/prepare`
- To jest dokładnie ten sam endpoint, który w `UC-12` odpowiada za techniczne przygotowanie danych do treningu i zapis jednego artefaktu `{datasetName}.npz`.
- W ramach tego refaktoru nie tworzymy nowego endpointu dla `UC-16` ani osobnego endpointu tylko do preview albo tylko do poprawy `board`.
- Zakres zmiany polega na tym, że ten sam workflow uruchamiany przez `POST /ml/datasets/prepare` ma:
  - lepiej budować `board` dla źródeł typu `board`,
  - lepiej przygotowywać końcowe komórki do treningu i ewaluacji,
  - zapisywać preview zgodne z rzeczywistym obrazem użytym w `.npz`.
- Innymi słowy: refaktor dotyczy środka istniejącego endpointu przygotowania datasetu, a nie nowego kontraktu HTTP.

## Problem
- W aktualnym `infrastructure` wykrycie planszy korzysta z preprocessingu `grayscale -> blur -> adaptive threshold`, ale po wykryciu krawędzi perspektywa jest transformowana na obrazie wejściowym w kolorze.
- W praktyce oznacza to, że:
  - logika detekcji działa na obrazie binarnym,
  - ale zapisany `correctedBoard` i dalsza ekstrakcja komórek startują z innej reprezentacji obrazu niż ta, która faktycznie posłużyła do znalezienia planszy,
  - finalne preview i artefakty datasetowe nie są intuicyjnie podobne do obrazu po binaryzacji i odwróceniu kolorów, którego oczekujemy przy przygotowaniu cyfr do odczytu.
- Dodatkowy objaw diagnostyczny jest taki, że na końcu niektóre podglądy wyglądają jak obrazy w różnych kolorach. To nie powinno mieć miejsca w finalnym przepływie przygotowania cyfr:
  - artefakty końcowe dla komórek powinny być jednokanałowe,
  - powinny być prezentowane jako `grayscale` / czarno-białe,
  - nie mogą polegać na pseudo-kolorowaniu wynikającym z domyślnego renderowania narzędzia wizualizacyjnego.

## Kontekst projektowy
- `draft` pozostaje wyłącznie miejscem eksperymentów i wzorcem referencyjnym.
- Docelowa zmiana dotyczy wyłącznie usług w `src/MachineLearning/infrastructure` oraz warstw, które je orkiestrują.
- `BE` pozostaje właścicielem workflow i `source of truth`; refaktor nie przenosi odpowiedzialności biznesowej do `ML`.
- Nie wprowadzamy nowego publicznego API dla `FE`; wykorzystujemy istniejące przepływy `BE -> ML`.
- Publicznym i technicznym punktem wejścia po stronie `ML` pozostaje `POST /ml/datasets/prepare`, konsumowany przez `BE` w workflow przygotowania danych treningowych.

## Stan docelowy

### 1. Spójny board pipeline
- Pipeline budowy `board` w `infrastructure` ma odtwarzać sprawdzony kierunek z `draft`:
  - przygotowanie obrazu,
  - redukcja szumu,
  - wzmocnienie kontrastu, jeśli jest potrzebne w przyjętej recepcie preprocessingu,
  - binaryzacja,
  - odwrócenie kolorów tam, gdzie jest to wymagane przez dalsze etapy,
  - wykrycie rodzin linii i rekonstrukcja logicznej ramki planszy,
  - korekcja perspektywy,
  - podział planszy na siatkę `9x9`.
- Obraz po korekcji perspektywy używany dalej do ekstrakcji komórek ma być zgodny z tą samą reprezentacją, na której zapadła decyzja o położeniu planszy.
- Niedopuszczalna jest sytuacja, w której detekcja planszy jest wykonywana na obrazie binarnym, ale `correctedBoard` wraca do kolorowego źródła bez jawnego powodu i bez zachowania tej samej semantyki obrazu.

### 2. Spójny cell pipeline
- Preprocessing pojedynczej komórki ma prowadzić do jednego kanonicznego wyniku używanego równocześnie do:
  - preview w `UC-16`,
  - zapisu danych do `.npz`,
  - treningu,
  - ewaluacji,
  - inferencji pojedynczej komórki, o ile profil wejściowy jest ten sam.
- Kanoniczny wynik końcowy powinien mieć postać:
  - obrazu jednokanałowego,
  - po binaryzacji i odwróceniu kolorów,
  - z foregroundem cyfry przygotowanym do wycentrowania,
  - po resize do ustalonego profilu wejściowego, domyślnie `28x28`,
  - bez dodatkowego kolorowania lub alternatywnej ścieżki tylko dla preview.
- `preview` ma być dokładnie tym samym obrazem, z którego później powstaje tablica `float32` do `.npz`.

### 3. Spójna reprezentacja wizualna
- Finalne artefakty preview dla cyfr i komórek nie mogą być zapisywane ani renderowane w sposób sugerujący różne mapy kolorów.
- Jeżeli artefakt jest obrazem końcowym po preprocessingu cyfry, to:
  - pozostaje jednokanałowy,
  - zapisujemy go jako obraz grayscale / binary,
  - renderowanie w notebooku, UI albo narzędziach pomocniczych ma jawnie traktować go jako `gray`, a nie zostawiać decyzję domyślnemu rendererowi.
- W szczególności należy wyeliminować rozjazd pomiędzy:
  - obrazem roboczym używanym przez model,
  - obrazem preview zapisywanym do diagnostyki,
  - obrazem pokazywanym użytkownikowi lub w notatniku.

## Zakres refaktoru

### W zakresie
- Uporządkowanie przepływu `board -> correctedBoard -> cells`, tak aby wszystkie etapy używały spójnej reprezentacji obrazu.
- Uporządkowanie końcowej recepty preprocessingu komórki w oparciu o wnioski z `draft`.
- Wyeliminowanie mieszania reprezentacji:
  - `BGR`,
  - `grayscale`,
  - `binary`,
  - `binary inverted`,
  - `float32 normalized`,
  bez jawnego kontraktu, po co i gdzie dana postać jest używana.
- Jawne określenie, który obraz jest:
  - artefaktem detekcji planszy,
  - artefaktem po warp,
  - artefaktem wejściowym do cięcia komórek,
  - artefaktem końcowym komórki do modelu,
  - artefaktem preview.
- Ujednolicenie przygotowania danych typu `board` z tym, jak mają wyglądać finalne próbki do treningu i ewaluacji.
- Doprecyzowanie kontraktu jakościowego dla preview w `UC-16`, tak aby preview odzwierciedlało rzeczywisty obraz użyty w `.npz`.

### Poza zakresem
- Zmiany w `src/MachineLearning/draft`.
- Dodawanie nowego publicznego endpointu dla `FE`.
- Dodawanie nowego wewnętrznego endpointu `ML` dla refaktoru `board` albo osobnego endpointu tylko do preview.
- Zmiana odpowiedzialności `BE` jako właściciela workflow.
- Zmiana formatu biznesowego `.npz`, jeśli obecny format pozostaje kompatybilny z docelowym profilem wejścia.
- Rozszerzanie tej historyjki o selekcję, usuwanie lub ręczne zatwierdzanie próbek.

## Główne decyzje projektowe

### 1. Draft jest wzorcem, nie kodem runtime
- `draft` służy do sprawdzania jakości i kolejności kroków.
- Kod produkcyjny nie importuje bezpośrednio modułów z `draft`.
- Refaktor polega na przełożeniu wniosków z eksperymentu na generyczne adaptery i pipeline'y w `infrastructure`.

### 2. Jeden kanoniczny obraz końcowy komórki
- Należy utrzymać jedną kanoniczną funkcję przygotowania komórki do postaci `uint8`, z której:
  - zapisujemy preview,
  - budujemy `float32` przez normalizację,
  - korzystamy podczas treningu i ewaluacji.
- Nie wolno utrzymywać osobnej, "ładniejszej" ścieżki do podglądu, jeśli odbiegałaby od danych treningowych.

### 3. Jawna semantyka obrazu planszy po warp
- W implementacji musi być jasno określone, który wariant obrazu jest zwracany jako `correctedBoard`.
- Jeżeli celem `correctedBoard` jest artefakt diagnostyczny "co model naprawdę widzi", to powinien być oparty o tę samą reprezentację po preprocessingu, a nie o surowe kolorowe wejście po samej transformacji perspektywicznej.
- Jeżeli potrzebujemy zachować także wersję kolorową do innych celów diagnostycznych, musi to być osobny, jawnie nazwany artefakt, a nie domyślny wynik tego samego pola.

### 4. Brak pseudo-kolorowania
- Artefakty końcowe dla komórek mają być przechowywane i pokazywane jako jednokanałowe.
- Narzędzia diagnostyczne muszą jawnie renderować takie obrazy w skali szarości.
- Nie dopuszczamy sytuacji, w której identyczny technicznie wynik w jednym miejscu jest szary, a w innym wygląda na kolorowy tylko dlatego, że renderer użył domyślnej mapy kolorów.

## Oczekiwane zmiany techniczne w ML
- Refaktor jest realizowany wewnątrz istniejącego handlera i pipeline'u obsługującego `POST /ml/datasets/prepare`.
- `board` detection i `board` warp powinny zwracać reprezentację zgodną z docelowym pipeline'em dalszego cięcia komórek.
- `board` extraction nie może mieszać bez uzasadnienia dwóch ścieżek:
  - binarnej do wykrycia,
  - kolorowej do końcowego `correctedBoard`.
- `cell_preprocessing_pipeline` pozostaje wspólnym miejscem budowania kanonicznego obrazu cyfry.
- Preview datasetowe w `UC-16` musi korzystać z dokładnie tego samego wyniku `uint8`, który później staje się `float32`.
- Wszelkie adaptery zapisu artefaktów obrazowych muszą zachować jednokanałowość i nie dodawać własnej interpretacji kolorów.

## Obsługa błędów
- `POST /ml/datasets/prepare` nie może zwracać pozornego sukcesu dla źródła typu `board`, jeśli w praktyce nie udało się znaleźć ani jednej poprawnej planszy.
- Jeżeli dla wybranego źródła `board`:
  - nie uda się wykryć żadnego `board`,
  - albo wszystkie wykryte kandydaty planszy odpadną podczas ekstrakcji / warp / cięcia komórek,
  to workflow ma zwrócić czytelną odpowiedź błędu zamiast tworzyć mylący wynik końcowy.
- Odpowiedź błędu powinna pozostać zgodna z istniejącym kontraktem `ErrorApiResponse`:
  - `errorType`
  - `message`
- Semantycznie ma to być błąd typu `422 Unprocessable Content`, bo źródło wejściowe zostało przyjęte technicznie, ale nie dało się z niego wyprowadzić poprawnej planszy treningowej.
- Rekomendowany `errorType` dla tego przypadku:
  - `board_not_found`
- Rekomendowany komunikat:
  - `Nie udało się wykryć żadnej poprawnej planszy Sudoku w źródle board.`
- To zachowanie dotyczy zarówno przypadku całkowitego braku planszy, jak i przypadku, w którym linie/ramka zostały wykryte błędnie i po walidacji nie pozostał ani jeden poprawny `board`.

## Kryteria akceptacji
- Żądanie `POST /ml/datasets/prepare` nadal pozostaje jedynym endpointem uruchamiającym przygotowanie datasetu i preview dla `UC-16`.
- Dla źródeł `board` obraz planszy po korekcji perspektywy i obraz używany do cięcia komórek są semantycznie spójne z wynikiem preprocessingu zastosowanym podczas detekcji planszy.
- Końcowe komórki przygotowane do datasetu, treningu i ewaluacji są wizualnie zbliżone do wyniku osiągniętego w `draft`: czarno-białe / grayscale, po odwróceniu kolorów i binaryzacji, bez losowych różnic reprezentacji.
- `preview` dla komórek nie odbiega od obrazu użytego w `.npz`; jest tym samym obrazem w formacie `uint8`.
- W diagnostyce nie pojawiają się "różne kolory" dla końcowych komórek wynikające z renderowania jednokanałowego obrazu jak mapy kolorów.
- Refaktor nie wymaga żadnej zmiany w `src/MachineLearning/draft`.
- Istniejące publiczne kontrakty `BE <-> ML` pozostają bez zbędnego rozszerzania.
- Jeżeli źródło typu `board` nie zawiera ani jednej poprawnie wykrytej planszy, `POST /ml/datasets/prepare` zwraca czytelny `ErrorApiResponse`, a nie sukces z pustym lub mylącym wynikiem.

## Ryzyka
- Zbyt szybkie spięcie logiki draftowej 1:1 może przenieść do runtime elementy eksperymentalne, które nie są jeszcze stabilne parametrycznie.
- Zmiana reprezentacji `correctedBoard` może wpłynąć na istniejące preview i testy integracyjne, nawet jeśli poprawi spójność merytoryczną.
- Jeśli nie zostanie jasno ustalone, który artefakt jest "diagnostyczny kolorowy", a który "kanoniczny dla modelu", zespół ponownie wróci do niejednoznaczności.

## Notatki implementacyjne
- Referencją analityczną dla kolejności kroków i oczekiwanego wyglądu artefaktów pozostaje `src/MachineLearning/draft/sudoku_board_threshold_experiment.ipynb` oraz powiązane moduły w `src/MachineLearning/draft`.
- Implementacja runtime powinna reuse'ować istniejące adaptery `infrastructure` wszędzie tam, gdzie da się zachować spójność bez duplikacji.
- Jeśli obecny podział odpowiedzialności między `board` a `cell preprocessing` utrudnia spójność obrazu końcowego, należy refaktoryzować kontrakty wewnętrzne tych usług, ale bez łamania publicznego przepływu `BE -> ML`.
