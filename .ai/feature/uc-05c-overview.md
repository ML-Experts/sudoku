# UC-05C — Historyjka scalona

## Status
Ta historyjka została scalona i nie jest już rozwijana jako osobny `UC`.

## Gdzie przeniesiono odpowiedzialności
- Budowa `recognizedGrid` i jego podstawowa prezentacja w `UI` zostały przeniesione do `UC-05A`.
- Aktualizacja tego samego widoku planszy podczas pracy solvera została przeniesiona do `UC-05E`.

## Powód scalenia
Poprzednia wersja `UC-05C` dublowała odpowiedzialności opisane już w `UC-05A` i częściowo w `UC-05E`, zwłaszcza:
- sposób nanoszenia cyfr do `recognizedGrid`,
- kontrakty transportowe dla danych rozpoznania,
- opis renderowania tego samego gridu w `UI`.

Pozostawienie osobnej historyjki zwiększało ryzyko niespójności dokumentacji i mnożenia endpointów bez wyraźnej wartości architektonicznej.

## Decyzja architektoniczna
Nie tworzymy osobnego endpointu tylko po to, żeby narysować siatkę 9×9.

W `UC-05` obowiązuje teraz podział:
- `UC-05A` -> inferencja pojedynczych komórek, złożenie `recognizedGrid`, podstawowa prezentacja stanu rozpoznanego,
- `UC-05B` -> start i logika backtrackingu,
- `UC-05D` -> overlay na obrazie,
- `UC-05E` -> live solve i aktualizacja tego samego gridu przez `SignalR`.

## Dalsze użycie identyfikatora
Plik zostaje zachowany celowo, żeby nie zrywać istniejących odwołań do `UC-05C` w dokumentacji roboczej, notatkach i rozmowach. Jego funkcją jest teraz wyłącznie wskazanie miejsca po scaleniu.
