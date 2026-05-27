# UC-16 — Przegląd przygotowanego datasetu i artefaktów preview

## Cel
- Umożliwić użytkownikowi obejrzenie tego, co system rzeczywiście zapisał podczas przygotowania datasetu.
- Oprzeć przegląd wyłącznie o artefakty zapisane już na dysku podczas `UC-12`, bez dodatkowego kroku zatwierdzania.
- Utrzymać `Backend` jako publiczny `source of truth` dla rekordów datasetów i referencji do preview.

## Historyjka
Jako operator ML chcę po przygotowaniu datasetu od razu obejrzeć w aplikacji zapisany `.npz`, metadane i artefakty preview, aby ocenić jakość preprocessingu przed użyciem datasetu do treningu.

## Główna zasada workflow
1. Użytkownik uruchamia przygotowanie datasetu.
2. System od razu zapisuje:
   - finalny `.npz`,
   - rekord metadanych,
   - artefakty preview do oglądania.
3. Dopiero po tym użytkownik ogląda dataset w `FE`.

W `UC-16` nie ma osobnego kroku `approve`, `finalize` ani `publish`.

## Zakres danych do podglądu
### `board`
- plansza po korekcji perspektywy tuż przed cięciem,
- wycięte elementy po preprocessingu, gotowe do wejścia do datasetu,
- metadane pochodzenia próbki, jeśli są dostępne w rekordzie przygotowania.

### `digit`
- finalne próbki po preprocessingu, gotowe do wejścia do datasetu,
- podstawowe metadane pochodzenia i etykiety, jeśli są dostępne.

## Zasady odpowiedzialności
### `Frontend`
- renderuje read-only przeglądarkę datasetu,
- nie zgaduje ścieżek plików i nie czyta katalogów bezpośrednio,
- korzysta wyłącznie z publicznego API `Backendu`.

### `Backend`
- przechowuje rekord datasetu i referencje do zapisanych artefaktów preview,
- udostępnia chronione endpointy odczytu list, detali i obrazów preview,
- nie wymaga od `FE` ponownego uruchamiania preprocessingu.

### `MachineLearning`
- zapisuje artefakty preview w trakcie przygotowania datasetu,
- nie wystawia publicznego endpointu dla `FE`,
- pozostaje usługą wewnętrzną wykorzystywaną przez `Backend`.

## Relacja do `UC-12`
- `UC-12` pozostaje odpowiedzialny za przygotowanie i zapis datasetu.
- `UC-16` rozszerza ten workflow o zapis artefaktów preview i ich późniejsze przeglądanie.
- `UC-16` nie zmienia podstawowej semantyki `UC-12`: wynik przygotowania datasetu jest zapisywany od razu.

## Poza zakresem
- odrzucanie pojedynczych `boardów`,
- odrzucanie pojedynczych komórek z planszy,
- odrzucanie pojedynczych `digitów`,
- przebudowa nowej wersji datasetu po decyzjach użytkownika,
- fizyczne kasowanie plików źródłowych albo preview.

Ten zakres należy do późniejszego `UC-17`.

## Kryteria akceptacji
- Po przygotowaniu datasetu użytkownik może wejść do jego przeglądarki bez ponownego uruchamiania przygotowania.
- Podgląd korzysta z artefaktów zapisanych wcześniej na dysku.
- Workflow nie zawiera osobnego zatwierdzania pomiędzy zapisem a oglądaniem.
- W `UC-16` wszystkie operacje mają charakter read-only.
