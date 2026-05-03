# Przegląd zakresu UC po rozbudowie UC-06

## Cel
Ten dokument zbiera decyzje zakresowe po rozbudowie `UC-06` oraz po dodaniu `UC-11`, `UC-12` i `UC-13`.

Nie zastępuje szczegółowych historyjek per warstwa. PRD pozostaje opisem zakresu projektu, a szczegółowe kontrakty i implementację rozwijamy w plikach `.ai/feature/*` oraz `.ai/implementation-plan/*`.

## UC-05 — rozpoznanie i rozwiązanie sudoku
Dotychczasowe `UC-05` jest za szerokie jako jedna szczegółowa historyjka implementacyjna. Produktowo pozostaje jednym strumieniem "rozwiąż sudoku z obrazu", ale implementacyjnie powinien zostać rozbity.

Rekomendowany podział:
- `UC-05A` — inferencja pojedynczej cyfry / komórki,
- `UC-05B` — backtracking dla rozpoznanego gridu,
- `UC-05C` — przypisanie cyfr do komórek i prezentacja w siatce 9×9,
- `UC-05D` — graficzne naniesienie cyfr na obraz.

Kontrakt inferencji pojedynczej komórki powinien bazować na `ImageApiEntry` (`mimeType` + `base64`) i zwracać minimalną odpowiedź `{ "digit": 1..9 | null }`. `null` oznacza brak rozpoznanej cyfry / pustą komórkę. Eksperyment `EXP-04` jest źródłem wniosków technicznych, ale nie jest docelowym publicznym API produktu.

Dla pełnej planszy nie przesądzamy na poziomie przeglądu, czy lepsze jest 81 osobnych requestów, batch, czy endpoint wyższego poziomu. Wariant 81 requestów jest dopuszczalny i może dać prosty progres po stronie `FE`, bo klient wie, które komórki wysłał i ile odpowiedzi już wróciło. Batch lub endpoint wyższego poziomu można rozważyć później, jeśli uprości to orkiestrację albo poprawi wydajność runtime.

## UC-06 — trening i model wynikowy
`UC-06` kończy się utworzeniem modelu wynikowego w `models/registry/{producedModelName}`.

Model zakończony sukcesem powinien mieć kompletny manifest techniczny `model.json`, tak aby mógł zostać później wybrany jako aktywny model inferencyjny w `UC-10`.

`UC-06` nie przełącza modelu aktywnego automatycznie. Odpowiada za:
- trening,
- zapis artefaktów,
- finalizację manifestu modelu wynikowego,
- status runu,
- relację `runName -> producedModelName`.

## UC-07 — postęp treningu
Po rozbudowie `UC-06` `UC-07` nie powinien wprowadzać nowego transportu ani nowych identyfikatorów runu.

Jego sens to rozwinięcie doświadczenia użytkownika:
- czytelny ekran postępu,
- komunikaty etapów,
- obsługa reconnect,
- prezentacja sukcesu, błędu i anulowania,
- ewentualny komunikat, że model wynikowy jest gotowy do wyboru w `UC-10`.

`UC-07` nie przełącza aktywnego modelu.

## UC-08 — lista treningów i modeli
`GET /api/models/registry` powstały w `UC-06` nie wyczerpuje sensu `UC-08`.

`UC-08` powinien rozwijać widok katalogowy:
- lista runów treningowych,
- lista modeli w rejestrze,
- wpisy bootstrap,
- modele wytrenowane w systemie,
- statusy i capabilities modeli,
- powiązania `runName -> producedModelName`,
- szybkie przejście do szczegółów runu lub modelu.

## UC-09 — szczegóły treningu i metryki
Jeśli podstawowy `GET /api/trainings/{runName}` istnieje już po `UC-06`, `UC-09` powinien rozwijać jego zawartość, a nie tylko samo istnienie endpointu.

Zakres `UC-09`:
- konfiguracja treningu,
- użyty dataset i model bazowy,
- `benchmarkName`,
- metryki,
- confusion matrix,
- raport ewaluacyjny,
- referencje do artefaktów raportu,
- dane potrzebne do porównania modeli.

Benchmark jest częścią konfiguracji i raportu treningowego, a nie osobnym celem samego endpointu.

## UC-10 — aktywny model inferencyjny
`UC-10` odpowiada za wybór i przełączenie aktywnego modelu.

Operacja powinna aktualizować lekki wskaźnik `models/active/inference.json`, bez kopiowania całego katalogu modelu. `UC-10` powinien dopuszczać tylko modele, które są kompletne i mają `canUseForInference = true`.

Po przełączeniu aktywnego modelu kolejne wywołania ścieżki inferencji i `UC-05` powinny korzystać z nowego modelu.
