## Sudoku Vision — rozpoznawanie i rozwiązywanie sudoku ze zdjęcia

### Skład zespołu
- **Imię Nazwisko** — (np. 123456)
- **Imię Nazwisko** — (np. 123456)
- **Imię Nazwisko** — (np. 123456)

### Role w zespole
- **ML / trening modelu**: <kto>
- **Computer Vision (OpenCV)**: <kto>
- **Solver (backtracking)**: <kto>
- **Integracja / API / UI**: <kto 1>, <kto 2> (może być kilka osób; interfejs użytkownika + spięcie end-to-end: web + C# ↔ Python (REST))
- **Ewaluacja / raport / prezentacja**: <kto 1>, <kto 2> (może być kilka osób; metryki jakości ML + wnioski; przygotowanie demo i slajdów)

---

### Historyjki (backlog) i przypisania (kto co bierze)
Poniższe ID odpowiadają backlogowi z PRD (sekcja 8). Uzupełnijcie osoby w kolumnach **INFRA/FE/BE/ML** (jeśli pozycja dotyczy kilku obszarów — wpiszcie osoby w kilku kolumnach; jeśli nie dotyczy — zostawcie `—`). **Uwaga**: przypadki użycia (UC) są przekrojowe, więc zwykle będą miały równolegle FE/BE/ML.

Skrótowo:
- **FE**: interfejs web
- **BE**: C# backend (ASP.NET Core Web API) + integracja z serwisem Python (REST)
- **ML**: model (trening + inferencja)
- **INFRA**: serwer/hosting, domena, SSL, reverse proxy, zabezpieczenia, uruchamianie usług, jakość, dokumentacja (CI/CD opcjonalnie)

| ID | Zakres | INFRA | FE | BE | ML |
|---|---|---|---|---|---|
| INF-01 | Szkielet repo + README + przykłady do demo | <kto> | — | — | — |
| INF-02 | Uruchomienie lokalne całego systemu (np. compose/skrypty) | <kto> | — | — | — |
| INF-03 | Serwer + domena + SSL + reverse proxy + zabezpieczenia | <kto> | — | — | — |
| INF-04 | Standardy jakości (pre-commit, zasady pracy) | <kto> | — | — | <kto> |
| INF-05 (opc.) | Serwer Jupyter (JupyterLab) | <kto> | — | — | <kto> |
| INF-06 (opc.) | CI na PR (lint/test/build) | <kto> | <kto> | <kto> | <kto> |
| INF-07 (opc.) | CD: deploy na serwer po merge/akceptacji PR | <kto> | <kto> | <kto> | <kto> |
| UC-01 | Upload pliku sudoku do biblioteki przykładów (examples) | — | <kto> | <kto> | — |
| UC-02 | Lista dostępnych przykładów sudoku | — | <kto> | <kto> | — |
| UC-03 | Pobierz wybrany plik przykładowy | — | <kto> | <kto> | — |
| UC-04 | Wybierz przykład do przetworzenia + wstępna obróbka | — | <kto> | <kto> | <kto> |
| UC-05 | Rozwiąż wybrany plik przez system | — | <kto> | <kto> | <kto> |
| UC-06 | Uruchom trening na dataset z data/raw | — | <kto> | <kto> | <kto> |
| UC-07 | Postęp treningu + informacja o zakończeniu | — | <kto> | <kto> | <kto> |
| UC-08 | Lista treningów i modeli | — | <kto> | <kto> | <kto> |
| UC-09 | Szczegóły treningu + metryki | — | <kto> | <kto> | <kto> |
| UC-10 | Wybór aktywnego modelu do inferencji | — | <kto> | <kto> | <kto> |
| UC-11 | Dodaj własny dataset do uczenia | — | <kto> | <kto> | <kto> |

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
│   ├── raw/
│   ├── processed/
│   ├── splits/
│   ├── models/
│   └── reports/
├── README.md
├── requirements.txt
└── examples/  (opcjonalnie)
```

Główne katalogi (do uzupełnienia pod Waszą implementację):
- `src/` — kod aplikacji (vision / ml / solver / render / interface)
- `data/` — robocze dane i artefakty ML (często większe; nie zawsze trzymane w repo)
  - `data/raw/` — pobrany dataset (albo instrukcja jak pobrać)
  - `data/processed/` — przetworzone wycinki/tenzory po pipeline (gotowe do treningu/ewaluacji)
  - `data/splits/` — podziały train/val/test (np. listy plików, CSV)
  - `data/models/` — zapisane modele/checkpointy
  - `data/reports/` — metryki, confusion matrix, wykresy/raporty
- `examples/` — przykładowe pliki do demo/szybkich testów end-to-end (wejścia i ewentualnie wyniki)

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

Docelowo: frontend web wysyła obraz do C# endpointu, a C# wywołuje serwis ML w Pythonie. Uzupełnijcie tutaj komendy uruchomienia frontendu, backendu i serwisu ML oraz przykładowe requesty (np. przez Swagger).

---

### Trening modelu
(Uzupełnijcie, jeśli trenujecie model w repo. Jeśli korzystacie z gotowego modelu — opiszcie skąd i jak go pobrać.)

Przykład:

```bash
python -m src.ml.train --data-dir "data/..." --out-models "data/models/model.pt"
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
- **Interface**: web UI + API.

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
