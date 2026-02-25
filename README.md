## Sudoku Vision — rozpoznawanie i rozwiązywanie sudoku ze zdjęcia

### Skład zespołu
- **Imię Nazwisko** — (np. 123456)
- **Imię Nazwisko** — (np. 123456)
- **Imię Nazwisko** — (np. 123456)

### Role w zespole
- **ML / trening modelu**: <kto>
- **Computer Vision (OpenCV)**: <kto>
- **Solver (backtracking)**: <kto>
- **Integracja / API / UI**: <kto 1>, <kto 2> (może być kilka osób; interfejs użytkownika + spięcie end-to-end; ambitny: web+C#↔Python REST; lekki: CLI/Streamlit)
- **Ewaluacja / raport / prezentacja**: <kto 1>, <kto 2> (może być kilka osób; metryki jakości ML + wnioski; przygotowanie demo i slajdów)

---

### Historyjki (backlog) i przypisania (kto co bierze)
Poniższe ID odpowiadają historyjkom z PRD. Uzupełnijcie osoby w kolumnach **FE/BE/ML/CV** (jeśli historyjka dotyczy wielu obszarów — wpiszcie osoby w kilku kolumnach; jeśli nie dotyczy — zostawcie `—`). **Uwaga**: wiele historyjek jest przekrojowych (end-to-end), więc jeśli w trakcie prac wyjdzie, że potrzebny jest też FE/BE/ML/CV — po prostu dopiszcie osoby w dodatkowych kolumnach.

Skrótowo:
- **FE**: interfejs (web / Streamlit)
- **BE**: API / „glue” (C# backend lub Python FastAPI/CLI, zależnie od wariantu)
- **ML**: model (trening + inferencja)
- **CV**: pipeline obrazu (OpenCV)

| ID | Zakres | FE | BE | ML | CV |
|---|---|---|---|---|---|
| US-01 | Wykrycie planszy + korekcja perspektywy (warp) | <kto> | <kto> | — | <kto> |
| US-02 | Cięcie na 81 komórek + wykrycie pustych pól | <kto> | <kto> | — | <kto> |
| US-03 | Dane + preprocessing + augmentacje + skrypt treningu | — | — | <kto> | <kto> |
| US-04 | Inferencja CNN: predykcja cyfr + budowa gridu 9×9 | — | <kto> | <kto> | <kto> |
| US-05 | Porównanie: własny CNN vs transfer learning + raport metryk | — | — | <kto> | — |
| US-06 | Solver sudoku (backtracking) + walidacja wejścia | — | <kto> | — | — |
| US-07 | Render overlay wyniku (opcjonalnie inverse warp na oryginał) | <kto> | <kto> | — | <kto> |
| US-08 | Interfejs użytkownika (CLI/mini-UI lub web) + prezentacja wyniku | <kto> | <kto> | — | — |
| US-09 | Integracja warstw + kontrakt wej./wyj. (API/CLI) | <kto> | <kto> | <kto> | — |
| US-10 | README + instrukcje uruchomienia + powtarzalność | — | <kto> | — | — |
| US-11 | Jakość kodu: pre-commit (black/isort/pyupgrade/pylint) + standardy commitów | — | <kto> | <kto> | <kto> |

---

### Opis funkcjonalny programu
Program potrafi:
- rozpoznać planszę Sudoku ze zdjęcia,
- wykryć i zidentyfikować cyfry w polach (ML/CNN w Pythonie),
- zbudować macierz 9×9 reprezentującą stan gry,
- rozwiązać sudoku algorytmem backtrackingu,
- wygenerować obraz wynikowy z naniesionymi cyframi na planszę.

---

### Wymagania środowiskowe
- **Python uruchamiany w środowisku Unix/Linux**: rekomendowane **WSL2 (Ubuntu)** na Windows.
- (Do uzupełnienia) Minimalne wersje: Python **3.14+** (uwaga: jeśli biblioteki nie wspierają 3.14, użyj 3.13/3.12), opcjonalnie CUDA, itp.

---

### Struktura repozytorium
Wymagana struktura:

```text
sudoku/
├── src/
├── data/
├── README.md
├── requirements.txt
└── examples/  (opcjonalnie)
```

Główne katalogi (do uzupełnienia pod Waszą implementację):
- `src/` — kod aplikacji (vision / ml / solver / render / interface)
- `data/` — dane treningowe/testowe oraz artefakty przetwarzania
- `examples/` — przykładowe wejścia/wyjścia do demo

---

### Instalacja
W środowisku Unix/WSL:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

(Jeśli używacie innego sposobu zarządzania zależnościami — opiszcie go tutaj.)

---

### Uruchomienie (inferencja end-to-end)
(Uzupełnijcie docelową komendę/entrypoint po implementacji.)

Przykład:

```bash
python -m src.cli --image "examples/input_01.jpg" --out-dir "examples/out_01"
```

Oczekiwane artefakty wyjściowe (przykład):
- `recognized_grid.json` — grid 9×9 (0 = puste)
- `solved_grid.json` — rozwiązany grid 9×9
- `overlay.png` — plansza z dopisanym rozwiązaniem

---

### Trening modelu
(Uzupełnijcie, jeśli trenujecie model w repo. Jeśli korzystacie z gotowego modelu — opiszcie skąd i jak go pobrać.)

Przykład:

```bash
python -m src.ml.train --data-dir "data/..." --out-model "data/models/model.pt"
```

---

### Ewaluacja jakości (metryki)
W raporcie pokazujemy co najmniej:
- accuracy,
- precision / recall / F1-score,
- confusion matrix,
- (opcjonalnie) porównanie: model własny vs transfer learning.

(Uzupełnijcie: gdzie jest skrypt/komenda do ewaluacji i gdzie zapisujecie wyniki.)

---

### Opis głównych funkcji / modułów
(Uzupełnijcie po implementacji; poniżej przykładowy szkielet.)

- **Vision (OpenCV)**: wykrycie planszy, korekcja perspektywy (`warpPerspective`), cięcie na 81 komórek, preprocessing.
- **ML (CNN, Python)**: klasyfikacja cyfry 1–9 (i/lub „empty”), przygotowanie wejścia 28×28, normalizacja 0–1.
- **Solver**: backtracking + walidacja reguł sudoku.
- **Render**: overlay rozwiązania na obraz i eksport wyników.
- **Interface**: CLI / (opcjonalnie) UI / (opcjonalnie) API.

---

### Podział pracy (kto co zrobił)
(Wypełnijcie konkretnie, pod ocenę pracy zespołowej.)

- **Osoba A**: <zakres>
- **Osoba B**: <zakres>
- **Osoba C**: <zakres>

---

### Ograniczenia i znane problemy
(Wypiszcie realne ograniczenia — to jest oczekiwane w projekcie.)

- <np. gorsze działanie przy mocnych cieniach / ręcznym piśmie / grubych liniach siatki>
- <np. konieczność korekty gridu w trudnych przypadkach>

---

### Zasady pracy w repozytorium (dla oceny)
- Każdy członek zespołu: **minimum 3 commity**.
- Commit messages: **opisowe** (np. `Add ...`, `Fix ...`, `Implement ...`).

---

### Prezentacja (5–7 minut) — checklist
- Demo działania aplikacji na kilku przykładach.
- Omówienie struktury rozwiązania (moduły i przepływ danych).
- Opis najważniejszych funkcji.
- Problemy napotkane + jak je rozwiązaliście.
