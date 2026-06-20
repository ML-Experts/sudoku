# UC-19-FE - Plan implementacyjny dla `GET /api/datasets/preparations/{preparationName}/board/folders`

## 1) Przeznaczenie endpointa
- Endpoint `GET /api/datasets/preparations/{preparationName}/board/folders` zwraca liste logicznych zrodel typu `board` dla wybranego `preparation`.
- W `UC-19` ten endpoint nie sluzy do przegladu plansz ani czyszczenia preparation jak w `UC-18`, tylko do zasilenia konfiguracji builda finalnego datasetu `.npz`.
- Z perspektywy `FE` endpoint:
  - pobiera kandydatow `board`, ktorzy moga trafic do payloadu `POST /api/datasets/processed`,
  - daje operatorowi liste nazw folderow, ktore beda potem mapowane na `sources[].name`,
  - nie pobiera `board/{sourceName}/files`,
  - nie pobiera `corrected-board.png`,
  - nie uruchamia delete,
  - nie wyznacza splitu po stronie backendu,
  - nie odczytuje bezposrednio struktury katalogow runtime.
- `Backend` pozostaje jedynym zrodlem prawdy dla:
  - istnienia `preparationName`,
  - listy zrodel `board`,
  - kolejnosci rekordow,
  - `totalCount`,
  - tego, czy wskazane `sourceName` jest legalnym wejsciem do dalszego builda.
- W `UC-19` odpowiedz tego endpointa jest tylko jednym z wejsc do formularza builda:
  - `board/folders` dostarcza zrodla typu `board`,
  - `digit/folders` dostarcza zrodla typu `digit`,
  - lokalny stan `FE` dopiero sklada z nich finalne drafty splitow.

## 2) Zakres planu
- Plan dotyczy wylacznie `FE`.
- Plan nie projektuje `BE` ani `ML`; uwzglednia tylko publiczny kontrakt endpointa i miejsce tego kroku w `UC-19`.
- Nie nalezy sugerowac sie obecna implementacja `BE` i `ML` poza ustalonym kontraktem use-case'u.
- Plan musi uwzglednic, ze ten endpoint jest juz zaadresowany w `UC-18`, wiec dla `UC-19` kluczowe jest:
  - reuse warstw wspolnych,
  - brak duplikacji klienta API,
  - brak bezposredniego couplingu `UC-19` do widoku browse/delete z `UC-18`.
- Plan jest warstwowy i trzyma MVVC:
  - `Model`,
  - `View`,
  - `ViewController`,
  - `Infrastructure`.
- Dokument opisuje tylko etap `board/folders`, ale pokazuje jego miejsce w szerszym flow `UC-19`, bo w przeciwnym razie latwo byloby przez pomylke reuse'owac zly ekran `UC-18`.

## 3) Miejsce endpointa w docelowym workflow `UC-19`
1. Uzytkownik wybiera `preparation` przez:
   - `GET /api/datasets/preparations`
   - `GET /api/datasets/preparations/{preparationName}`.
2. `FE` potwierdza, ze wybrane `preparationName` nadal jest poprawne i gotowe do dalszego kroku.
3. `FE` wywoluje `GET /api/datasets/preparations/{preparationName}/board/folders`.
4. `BE` zwraca logiczna liste nazw folderow `board`.
5. `FE` renderuje te nazwy jako kandydatow do wlaczenia w build `.npz`.
6. Operator:
   - zaznacza, ktore zrodla `board` maja wejsc do builda,
   - przypisuje im splity `mix` albo `train/val/test`,
   - nie oglada jeszcze listy plansz.
7. Rownolegle lub zaraz po tym `FE` pobiera `digit/folders`.
8. Dopiero po zebraniu zrodel `board` i `digit` `FE` sklada payload do `POST /api/datasets/processed`.

Wniosek:
- W `UC-19` `board/folders` jest krokiem konfiguracji builda, a nie krokiem eksploracji preparation.
- Nie wolno reuse'owac calego ekranu `Uc18BoardFoldersSection`, bo jego semantyka dotyczy innego celu biznesowego.

## 4) Glowne zalozenia architektoniczne
- Aktualna architektura FE formalnie pozostaje `TBD`, ale repo jest praktycznie:
  - `feature-based`,
  - warstwowe,
  - z rozdzialem `app`, `features`, `api`, `shared`, `types`.
- Dla tego endpointa nalezy utrzymac podzial:
  - `Model`: kontrakt transportowy, lokalny model zrodla `board` dla `UC-19`, lokalne reguly draftu splitow,
  - `View`: lista zrodel `board`, checkbox / akcja wlaczenia, kontrolki splitow, stany `loading/error/empty/success`,
  - `ViewController`: pobranie listy, abort, retry, utrzymanie draftow zrodel, reset nieaktualnych wpisow po refreshu,
  - `Infrastructure`: klient HTTP, walidacja JSON, mapowanie bledow.
- `FE` nie moze:
  - skanowac katalogow,
  - zgadywac listy `board` na podstawie details endpointu,
  - budowac listy z `UC-18` przez import calego komponentu,
  - rozmawiac z `ML`,
  - traktowac `board/folders` jako trigger do eager-loadu `board/files`.
- Zasada generycznosci:
  - usluga HTTP juz jest generyczna po `folderType`,
  - nie trzeba tworzyc nowego klienta tylko dla `UC-19`,
  - nowa logika ma byc generyczna tam, gdzie dotyczy ladowania listy folderow,
  - ale domena i widok `UC-19` moga pozostac endpoint-specific, bo maja inna semantyke niz `UC-18`.
- Zasada warstwowa:
  - `Infrastructure` ma tylko pobrac i zwalidowac kontrakt,
  - `ViewController` ma zrobic stan listy i draftow,
  - `Model` ma pilnowac zgodnosci selection oraz splitow,
  - `View` ma byc cienki i nie zawierac `fetch`.

## 5) Co juz istnieje i nalezy reuse'owac
- Istnieje klient HTTP preparation:
  - `src/Frontend/src/api/datasetPreparations.ts`
- Istnieje helper transportowy:
  - `src/Frontend/src/api/shared/fetchJson.ts`
- Istnieja kontrakty API:
  - `src/Frontend/src/types/api.ts`
- Istnieje juz transport dla tego endpointa:
  - `getDatasetPreparationFolders(apiBaseUrl, preparationName, folderType, accessToken, signal)`
- Istnieje juz guard odpowiedzi:
  - `isDatasetPreparationFoldersApiResponse()`
- Istnieje juz `UC-18`-owy model listy folderow:
  - `src/Frontend/src/features/uc18/domain/mapDatasetPreparationFoldersToDomain.ts`
  - `src/Frontend/src/features/uc18/domain/uc18PreparationFolder.ts`
  - `src/Frontend/src/features/uc18/domain/toUc18PreparationFolderKey.ts`
  - `src/Frontend/src/features/uc18/domain/reconcileSelectedPreparationFolder.ts`
- Istnieje juz `UC-18`-owy hook pobierania:
  - `src/Frontend/src/features/uc18/application/useUc18BoardFolders.ts`
- Istnieje juz shell `UC-19` dla wyboru preparation:
  - `src/Frontend/src/features/uc19/api/Uc19PreparationSelectionSection.tsx`
  - `src/Frontend/src/features/uc19/application/useUc19PreparationSelection.ts`
- Istnieje juz shell aplikacji:
  - `src/Frontend/src/app/views/DatasetsView.tsx`
  - `src/Frontend/src/app/state.ts`

Wniosek:
- Nie dodawac nowego klienta HTTP.
- Nie dodawac nowego kontraktu transportowego.
- Nie importowac bezposrednio `useUc18BoardFolders()` do `UC-19`, bo hook ma semantyke:
  - pojedynczego aktywnego `sourceName`,
  - przygotowania do `board/files`,
  - browse/delete flow.
- Dla `UC-19` trzeba reuse'owac warstwe `Infrastructure`, ale zbudowac osobny `Model` i `ViewController`.

## 6) Model API w komunikacji z `BE`

### 6.1 Request `FE -> BE`
- Metoda i sciezka:
  - `GET /api/datasets/preparations/{preparationName}/board/folders`
- Path params:
  - `preparationName: string`
- Query params:
  - brak
- Body:
  - brak
- Naglowki:
  - `Accept: application/json`
  - `Authorization: Bearer <token>` gdy istnieje sesja administratora

### 6.2 Model wejsciowy
- Brak payloadu JSON.
- Jedyna dana wejsciowa to poprawny `preparationName`.

### 6.3 Model wyjsciowy sukcesu
- `DatasetPreparationFoldersApiResponse`
  - `preparationName: string`
  - `type: string`
  - `items: string[]`
  - `totalCount: number`

Przyklad:

```json
{
  "preparationName": "preparation-001",
  "type": "board",
  "items": [
    "v1_training",
    "v2_training"
  ],
  "totalCount": 2
}
```

### 6.4 Model bledu
- `ErrorApiResponse`
  - `errorType: string`
  - `message: string`

### 6.5 Reguly kontraktowe
- Nie zmieniac nazw:
  - `DatasetPreparationFoldersApiResponse`
  - `ErrorApiResponse`
- Dane transportowe pozostaja w `camelCase`.
- `type` w transporcie pozostaje `string`.
- Dla tego endpointa `FE` oczekuje finalnie `type === "board"`.
- Odpowiedz `200` z `type != "board"` jest bledem kontraktu, a nie czesciowym sukcesem.
- `items` to nazwy folderow, ktore pozniej maja byc kopiowane 1:1 do:
  - `CreateProcessedDatasetApiEntry.sources[].name`
- `FE` nie moze:
  - normalizowac wielkosci liter,
  - obcinac nazw,
  - deduplikowac po swojemu,
  - sortowac alfabetycznie bez wymagania.

## 7) Zachowanie z kazdej warstwy MVVC

### Model
- Obejmuje:
  - transport `DatasetPreparationFoldersApiResponse`,
  - lokalny model `UC-19` dla zrodla `board`,
  - lokalny draft splitow dla pojedynczego zrodla,
  - logike pogodzenia draftow po refreshu,
  - regule "mix wyklucza train/val/test".
- `Model` nie zna:
  - Reacta,
  - `fetch`,
  - `AbortController`,
  - statusow HTTP.

### View
- Obejmuje:
  - panel listy zrodel `board` w `UC-19`,
  - licznik rekordow,
  - akcje `Odswiez liste board`,
  - stany `loading/error/empty/success`,
  - lokalna interakcje:
    - wlacz / wylacz zrodlo,
    - ustaw splity,
    - pokaz, ktore zrodla sa wybrane do builda.
- `View` nie:
  - buduje URL-i,
  - nie waliduje kontraktu,
  - nie pobiera `board/files`,
  - nie resetuje sesji.

### ViewController
- Obejmuje:
  - `loadBoardFolders(preparationName)`,
  - `retryLoadBoardFolders()`,
  - utrzymanie listy zrodel,
  - utrzymanie lokalnych draftow splitow,
  - pogodzenie draftow po refreshu,
  - `AbortController`,
  - reakcje na `401`,
  - wyczyszczenie zrodel po zmianie `preparationName`,
  - lekkie logowanie diagnostyczne.
- `ViewController` dla `UC-19` nie powinien:
  - dziedziczyc po widoku `UC-18`,
  - przechowywac pojedynczego `selectedSourceName` jak `UC-18`,
  - byc zalezny od preview / delete flow.

### Infrastructure
- Obejmuje:
  - `getDatasetPreparationFolders()`,
  - `fetchJson()`,
  - guard odpowiedzi JSON,
  - `buildAuthHeaders()`,
  - mapowanie bledow na `DatasetPreparationsApiError`.
- To jest juz gotowe i powinno byc reuse'owane bez duplikacji.

## 8) Pliki per warstwa i odpowiedzialnosci

### 8.1 View
- `[REUSE + ADJUST]` `src/Frontend/src/features/uc19/api/Uc19PreparationSelectionSection.tsx`
  - pozostaje ekranem wejscia do `UC-19`;
  - po potwierdzeniu gotowego `preparation` powinien osadzic lub otwierac krok listy zrodel `board` dla builda;
  - nie powinien juz odsyac operatora do pelnego ekranu browse `UC-18`, jesli celem jest konfiguracja builda.
- `[ADD]` `src/Frontend/src/features/uc19/api/Uc19BoardFoldersSelectionSection.tsx`
  - glowny widok endpointa `board/folders` w kontekscie `UC-19`;
  - renderuje liste zrodel `board`,
  - pokazuje zaznaczenie zrodel do builda,
  - pokazuje kontrolki splitow per zrodlo,
  - nie zna `fetch`.
- `[ADD]` `src/Frontend/src/features/uc19/api/Uc19BoardSourceSplitList.tsx`
  - czysto prezentacyjna lista rekordow `board`;
  - renderuje:
    - nazwe folderu,
    - wlaczenie / wylaczenie,
    - split chips / checkboxy,
    - lokalne hinty walidacyjne.
- `[REUSE]` `src/Frontend/src/features/uc19/api/index.ts`
  - publiczny entry point feature'a `UC-19`.
- `[REUSE + ADJUST]` `src/Frontend/src/app/views/DatasetsView.tsx`
  - utrzymuje shell krokow datasetowych;
  - nie powinien importowac `Uc18BoardFoldersSection` jako docelowego kroku konfiguracji builda, jesli `UC-19` dostanie wlasny panel zrodel.
- `[REUSE]` `src/Frontend/src/styles/datasets.css`
  - style listy, badge'y, chips splitow, bannerow i disabled state.

### 8.2 ViewController
- `[ADD]` `src/Frontend/src/features/uc19/application/useUc19BoardFoldersSelection.ts`
  - glowny hook use-case'u dla `board/folders` w `UC-19`;
  - pobiera liste zrodel `board`,
  - utrzymuje drafty zrodel wybranych do builda,
  - wspiera retry, abort i reset po zmianie `preparationName`.
- `[ADD]` `src/Frontend/src/features/uc19/application/uc19BoardFoldersSelectionReducer.ts`
  - reduktor czystego stanu listy i draftow.
- `[ADD]` `src/Frontend/src/features/uc19/application/uc19BoardFoldersSelectionTypes.ts`
  - typy stanu, akcji i interfejs publiczny hooka.
- `[REUSE]` `src/Frontend/src/features/uc19/application/useUc19PreparationSelection.ts`
  - dostarcza wybrane `preparationName` i gating do wejscia w krok `board/folders`.
- `[CONTEXT ONLY]` `src/Frontend/src/features/uc18/application/useUc18BoardFolders.ts`
  - zrodlo wzorca request + abort + retry + logging;
  - nie powinien byc importowany 1:1 do `UC-19`, bo niesie zla semantyke selection.

### 8.3 Model
- `[REUSE]` `src/Frontend/src/types/api.ts`
  - zrodlo prawdy dla `DatasetPreparationFoldersApiResponse`.
- `[ADD]` `src/Frontend/src/features/uc19/domain/uc19BoardSourceDraft.ts`
  - lokalny model domenowy rekordu `board` dla builda;
  - np.:
    - `preparationName`
    - `folderName`
    - `type`
    - `key`
    - `enabled`
    - `splits`
- `[ADD]` `src/Frontend/src/features/uc19/domain/mapDatasetPreparationBoardFoldersToDrafts.ts`
  - mapuje transport do lokalnych draftow `UC-19`;
  - pilnuje `type === "board"`.
- `[ADD]` `src/Frontend/src/features/uc19/domain/reconcileUc19BoardSourceDrafts.ts`
  - po refreshu zachowuje tylko te drafty, ktore nadal istnieja w odpowiedzi backendu;
  - usuwa nieaktualne wpisy.
- `[ADD]` `src/Frontend/src/features/uc19/domain/toggleUc19BoardSourceSplit.ts`
  - czysta logika zmiany splitow dla jednego rekordu.
- `[ADD]` `src/Frontend/src/features/uc19/domain/validateUc19BoardSourceDraft.ts`
  - sprawdza, czy wybrane zrodlo ma poprawny stan splitow.
- `[CONTEXT ONLY]` `src/Frontend/src/features/uc18/domain/mapDatasetPreparationFoldersToDomain.ts`
  - wzorzec mapowania transport -> lokalny model;
  - nie trzeba go reuse'owac bezposrednio, jesli `UC-19` potrzebuje inny model domenowy.

### 8.4 Infrastructure
- `[REUSE]` `src/Frontend/src/api/datasetPreparations.ts`
  - klient HTTP:
    - `getDatasetPreparationFolders()`
    - `isDatasetPreparationFoldersApiResponse()`
- `[REUSE]` `src/Frontend/src/api/shared/fetchJson.ts`
  - wspolny mechanizm:
    - `fetch`
    - parse
    - validate
    - errorFactory

### 8.5 Pliki sasiednie i downstream
- `[DOWNSTREAM / REUSE LATER]` `src/Frontend/src/api/datasets.ts`
  - tu znajduje sie obecny klient `POST /api/datasets/processed`;
  - osobny plan powinien zrefaktorowac go z modelu `raw` na model `preparation`.
- `[DOWNSTREAM / REUSE LATER]` `src/Frontend/src/features/uc18/application/useUc18DigitFolders.ts`
  - analogiczny endpoint dla `digit/folders`.
- `[CONTEXT ONLY]` `src/Frontend/src/features/uc18/api/Uc18BoardFoldersSection.tsx`
  - ekran browse/delete preparation;
  - nie jest docelowym ekranem konfiguracji builda.
- `[LEGACY / NIE ROZWIJAC]` `src/Frontend/src/components/Uc12DatasetPreparationSection.tsx`
  - stary workflow `raw -> processed`;
  - nie powinien byc fallbackiem dla `UC-19`.

## 9) Co nalezy dodac lub dopracowac
- Nie trzeba dodawac nowego klienta HTTP ani nowego typu transportowego.
- Trzeba dodac osobny `UC-19`-owy stan i widok dla `board/folders`, bo obecny `UC-18`:
  - pracuje na pojedynczym `selectedSourceName`,
  - prowadzi do `board/files`,
  - ma semantyke przegladu i czyszczenia, nie konfiguracji builda.
- Lokalny model `UC-19` musi wspierac:
  - wiele zaznaczonych zrodel,
  - osobne splity per zrodlo,
  - walidacje `mix` vs `train/val/test`,
  - bezpieczne pogodzenie stanu po odswiezeniu listy.
- Jesli JSX w `Uc19PreparationSelectionSection.tsx` zrobi sie zbyt duzy:
  - wydzielic panel `Uc19BoardFoldersSelectionSection`,
  - ale nie przenosic logiki requestow do komponentu prezentacyjnego.

## 10) Glowne funkcje
- `getDatasetPreparationFolders()`
- `isDatasetPreparationFoldersApiResponse()`
- `useUc19BoardFoldersSelection()`
- `loadBoardFolders()`
- `retryLoadBoardFolders()`
- `toggleBoardSourceEnabled()`
- `toggleUc19BoardSourceSplit()`
- `updateBoardSourceSplits()`
- `reconcileUc19BoardSourceDrafts()`
- `validateUc19BoardSourceDraft()`
- `mapDatasetPreparationBoardFoldersToDrafts()`
- `Uc19BoardFoldersSelectionSection()`
- `Uc19BoardSourceSplitList()`
- `fetchJson()`

## 11) Zachowanie endpointa w `UC-19`
- Po poprawnym wyborze `preparationName` widok uruchamia pobranie listy `board/folders`.
- Widok pokazuje:
  - nazwe wybranego `preparation`,
  - licznik `totalCount`,
  - liste nazw folderow,
  - stan zaznaczenia do builda,
  - lokalne splity per zrodlo,
  - przycisk odswiezenia.
- Endpoint nie powinien:
  - otwierac listy plansz,
  - ladowac obrazu preview,
  - wykonywac usuwania,
  - przygotowywac requestu do `board/files`.
- Po zaznaczeniu zrodla operator ustawia splity lokalnie, a `FE` trzyma draft do czasu finalnego `POST /api/datasets/processed`.
- Odwzorowanie na payload downstream:
  - `folderName` z odpowiedzi backendu -> `sources[].name`
  - stale `type = "board"` -> `sources[].type`
  - lokalny stan splitow -> `sources[].splits`

## 12) Specyficzna logika i pseudokod

### 12.1 Ladowanie listy `board/folders`

```text
loadBoardFolders(preparationName):
  normalizedPreparationName = preparationName.trim()

  if normalizedPreparationName is empty:
    reset state
    return

  abort previous request
  set state = loading

  response = getDatasetPreparationFolders(
    apiBaseUrl,
    normalizedPreparationName,
    "board",
    accessToken,
    signal
  )

  drafts = mapDatasetPreparationBoardFoldersToDrafts(response)
  reconciledDrafts = reconcileUc19BoardSourceDrafts(previousDrafts, drafts)

  set state = success(reconciledDrafts, response.totalCount)
```

### 12.2 Mapowanie transportu do lokalnego modelu `UC-19`

```text
mapDatasetPreparationBoardFoldersToDrafts(response):
  if response.type != "board":
    throw contract error

  return response.items.map(folderName => ({
    key: `board:${folderName}`,
    preparationName: response.preparationName,
    folderName,
    type: "board",
    enabled: false,
    splits: []
  }))
```

### 12.3 Pogodzenie draftow po refreshu

```text
reconcileUc19BoardSourceDrafts(previousDrafts, freshDrafts):
  byName = map previousDrafts by folderName

  result = []
  removedDrafts = []

  for each freshDraft in freshDrafts:
    previous = byName[freshDraft.folderName]

    if previous exists:
      result.push({
        ...freshDraft,
        enabled: previous.enabled,
        splits: previous.splits
      })
    else:
      result.push(freshDraft)

  for each previousDraft in previousDrafts:
    if not freshDrafts contains previousDraft.folderName and previousDraft.enabled:
      removedDrafts.push(previousDraft.folderName)

  return { drafts: result, removedDrafts }
```

### 12.4 Zmiana splitow dla pojedynczego zrodla

```text
toggleUc19BoardSourceSplit(previousSplits, split):
  if split == "mix":
    return previousSplits includes "mix" ? [] : ["mix"]

  withoutMix = previousSplits.filter(item => item != "mix")

  if withoutMix includes split:
    return withoutMix.filter(item => item != split)

  return [...withoutMix, split]
```

### 12.5 Walidacja pojedynczego draftu

```text
validateUc19BoardSourceDraft(draft):
  if draft.enabled is false:
    return valid

  if draft.splits.length == 0:
    return invalid("Wybierz split dla zrodla board.")

  if draft.splits includes "mix" and draft.splits.length > 1:
    return invalid("Split mix nie moze byc laczony z train/val/test.")

  return valid
```

## 13) Wyjatki, fallbacki i zachowanie bledowe

### 13.1 Statusy HTTP
- `200 OK`
  - lista poprawna;
  - moze byc pusta.
- `401 Unauthorized`
  - sesja administratora wygasla albo token jest niepoprawny;
  - `FE` wywoluje `onUnauthorized()`.
- `403 Forbidden`
  - operator nie ma dostepu do kroku administracyjnego;
  - `FE` pokazuje blad bez automatycznego retry.
- `404 Not Found`
  - `preparationName` nie istnieje albo zostalo usuniete;
  - `FE` traktuje to jako stale wejscie i blokuje dalsza konfiguracje.
- `500 Internal Server Error`
  - blad backendu.
- `502`, `503`, `504`
  - blad infrastrukturalny na sciezce przegladarka -> nginx -> backend.

### 13.2 Bledy kontraktu
- Jesli odpowiedz `200` ma zly ksztalt:
  - traktowac jako blad techniczny,
  - nie zamieniac tego na pusta liste,
  - nie zgadywac brakujacych pol.
- Jesli `/board/folders` zwroci `type = "digit"` albo inny typ:
  - traktowac jako blad kontraktu,
  - nie renderowac listy jako sukcesu.

### 13.3 Fallbacki dopuszczalne
- Zachowanie poprzedniej listy podczas kolejnego `loading` dla tego samego `preparationName`.
- Zachowanie poprzednich draftow tylko dla zrodel, ktore nadal istnieja po refreshu.
- Zachowanie poprzedniej listy przy chwilowym `5xx`, jesli `preparationName` sie nie zmienil.
- Wyczyszczenie tylko tych draftow, ktore zniknely z odpowiedzi backendu.

### 13.4 Fallbacki niedopuszczalne
- Zgadywanie listy `board` na podstawie:
  - `details.sources`,
  - `UC-18` cache'a widoku browse,
  - innych endpointow.
- Samodzielne sortowanie odpowiedzi po stronie FE bez wymagania.
- Hurtowe pobieranie `board/{sourceName}/files` po sukcesie `board/folders`.
- Przejscie `FE -> ML`.
- Reuse calego `Uc18BoardFoldersSection` jako gotowego kroku builda.

### 13.5 Zachowanie UI
- `idle`
  - brak poprawnego `preparationName`.
- `loading`
  - pokazuje banner ladowania;
  - moze zachowac poprzednia liste dla tego samego `preparationName`.
- `error`
  - pokazuje blad i blokuje dalszy krok.
- `success + empty`
  - pokazuje informacje, ze preparation nie ma zrodel `board`.
- `success + data`
  - lista jest interaktywna i pozwala:
    - wlaczyc zrodlo do builda,
    - ustawic splity.

## 14) Logging i diagnostyka FE
- Logowanie ma pomagac diagnozowac problemy, ale nie moze spamowac.

### `console.info`
- start ladowania `board/folders`,
- reczne odswiezenie listy,
- sukces pobrania listy wraz z `totalCount`,
- liczba aktualnie zaznaczonych zrodel po zmianie, jesli ma wartosc diagnostyczna.

### `console.warn`
- `401` i czyszczenie sesji,
- `404` dla stalego `preparationName`,
- usuniecie zaznaczonego draftu po odswiezeniu,
- proba przejscia dalej z niepoprawnymi splitami.

### `console.error`
- `5xx`,
- bledny ksztalt odpowiedzi,
- niespojny `type`,
- nieprzetwarzalna odpowiedz backendu.

### Guardraile logowania
- nie logowac tokena,
- nie logowac pelnej odpowiedzi backendu,
- nie logowac calej listy `items`,
- nie logowac kazdego rerenderu,
- logowac tylko lekkie metadane:
  - `preparationName`,
  - `type`,
  - `httpStatus`,
  - `errorType`,
  - `totalCount`,
  - `selectedCount`,
  - `removedDraftsCount`.

## 15) Mermaid flowchart - flow modeli

```mermaid
flowchart TD
    A["datasetPreparations.ts::getDatasetPreparationFolders()<br/>pobiera DatasetPreparationFoldersApiResponse"] --> B["types/api.ts::DatasetPreparationFoldersApiResponse<br/>kontrakt HTTP"]
    B --> C["uc19/domain/mapDatasetPreparationBoardFoldersToDrafts()<br/>mapuje items do draftow UC-19"]
    C --> D["uc19/domain/uc19BoardSourceDraft.ts<br/>lokalny model z enabled + splits"]
    D --> E["uc19/domain/reconcileUc19BoardSourceDrafts()<br/>utrzymuje drafty po refreshu"]
    E --> F["uc19/domain/validateUc19BoardSourceDraft()<br/>pilnuje poprawnych splitow"]
    F --> G["uc19/application/useUc19BoardFoldersSelection()<br/>zapisuje stan hooka"]
```

## 16) Mermaid flowchart - logika aplikacji z funkcjami

```mermaid
flowchart TD
    A["DatasetsView.tsx::renderUc19Step()<br/>osadza UC-19"] --> B["Uc19PreparationSelectionSection.tsx::render()<br/>wybor preparation"]
    B --> C["useUc19PreparationSelection.ts::canContinueToSources<br/>odblokowuje krok board/folders"]
    C --> D["Uc19BoardFoldersSelectionSection.tsx::mountSection()<br/>render sekcji board"]
    D --> E["useUc19BoardFoldersSelection.ts::loadBoardFolders()<br/>start pobrania"]
    E --> F["datasetPreparations.ts::getDatasetPreparationFolders()<br/>GET /api/datasets/preparations/{preparationName}/board/folders"]
    F --> G["fetchJson.ts::fetchJson()<br/>status + parse + validate"]
    G --> H["mapDatasetPreparationBoardFoldersToDrafts()<br/>mapowanie do modelu UC-19"]
    H --> I["reconcileUc19BoardSourceDrafts()<br/>utrzymanie draftow po refreshu"]
    I --> J["uc19BoardFoldersSelectionReducer.ts::loadSucceeded<br/>zapis listy i draftow"]
    J --> K["Uc19BoardSourceSplitList.tsx::renderRows()<br/>render wyboru zrodel i splitow"]
    K --> L["toggleUc19BoardSourceSplit()<br/>zmiana splitu dla rekordu"]
```

## 17) Opis przeplywu w obrebie `BE` potrzebny frontendowi
Ta sekcja opisuje tylko kontraktowe minimum potrzebne `FE`.

1. `FE` wysyla `GET /api/datasets/preparations/{preparationName}/board/folders`.
2. `BE` weryfikuje autoryzacje.
3. `BE` rozpoznaje `preparationName`.
4. `BE` odczytuje logiczna liste zrodel typu `board`.
5. `BE` zwraca:
   - `preparationName`,
   - `type = "board"`,
   - `items`,
   - `totalCount`.
6. `BE` nie powinien wywolywac `ML` dla tego endpointa.
7. `FE` nie powinien zakladac nic o fizycznym layoutcie katalogow poza semantyka kontraktu.

## 18) Workflow GitHub i runtime
- Dla tego endpointa nie jest potrzebna nowa zmienna srodowiskowa FE.
- Obowiazujacy workflow:
  - `.github/workflows/frontend-cd.yml`
  - buduje FE z:
    - `VITE_API_BASE_URL="${FE_VITE_API_BASE_URL:-/api}"`.
- W local:
  - `FE` powinien dzialac na stalym `/api` albo lokalnym `VITE_API_BASE_URL`;
  - po stronie FE nie dotykamy `appsettings`.
- W produkcji:
  - workflow backendowy moze podstawic produkcyjne `appsettings`,
  - ten plan FE nie moze od tego zalezec inaczej niz przez publiczny adres `/api`.
- Wniosek:
  - nie dodawac nowego env-a,
  - nie hardcodowac URL-i produkcyjnych,
  - nie traktowac workflow jako zrodla prawdy dla listy `board`.

## 19) Kolejnosc implementacji kodu dla historyjki
1. Zweryfikowac istniejacy kontrakt `DatasetPreparationFoldersApiResponse` w `src/Frontend/src/types/api.ts`.
2. Zweryfikowac, ze `src/Frontend/src/api/datasetPreparations.ts` pozostaje jedynym klientem `board/folders`.
3. Dodac model domenowy `UC-19` dla zrodla `board` i helpery splitow.
4. Dodac typy stanu i reducer `UC-19` dla listy `board/folders`.
5. Dodac hook `useUc19BoardFoldersSelection()`.
6. Dodac widoki `Uc19BoardFoldersSelectionSection.tsx` i `Uc19BoardSourceSplitList.tsx`.
7. Spiac nowy panel z `useUc19PreparationSelection()` tak, aby pojawial sie dopiero po poprawnym wyborze `preparation`.
8. Dopracowac logowanie diagnostyczne.
9. Podpiac stan wybranych zrodel `board` pod dalszy plan dla `POST /api/datasets/processed`.
10. Uruchomic kontrole jakosci FE.

## 20) Guardraile implementacyjne
- Nie tworzyc nowego klienta HTTP dla `board/folders`.
- Nie kopiowac logiki `useUc18BoardFolders()` 1:1 do `UC-19`.
- Nie importowac calego `Uc18BoardFoldersSection.tsx` do `UC-19`.
- Nie przenosic `fetch` do komponentow React.
- Nie traktowac `items: []` jako bledu.
- Nie pobierac `board/files` w ramach tego kroku.
- Nie zgadywac `sources[].name` z innych danych niz odpowiedz tego endpointa.
- Nie zmieniac istniejacych nazw typow transportowych.
- Nie mieszac konfiguracji builda `UC-19` z browse/delete z `UC-18`.
- Nie dodawac ciezkiego logowania ani `console.log` na kazda akcje UI.

## 21) Zaleznosci pomiedzy historyjkami

### Wejsciowe
- `UC-13`
  - dostarcza sesje administracyjna i token.
- `UC-17 GET /api/datasets/preparations`
  - daje liste preparation do wyboru.
- `UC-17 GET /api/datasets/preparations/{preparationName}`
  - potwierdza gotowosc wybranego preparation przed `board/folders`.

### Sasiednie
- `UC-18 GET /api/datasets/preparations/{preparationName}/board/folders`
  - istnieje juz jako krok browse;
  - w `UC-19` reuse'ujemy kontrakt i infrastrukture, ale nie caly widok.
- `UC-18 GET /api/datasets/preparations/{preparationName}/digit/folders`
  - powinien miec analogiczny model konfiguracji builda dla zrodel `digit`.

### Wyjsciowe
- `UC-19 POST /api/datasets/processed`
  - konsumuje `folderName` jako `sources[].name` i lokalne `splits`.
- `UC-06`
  - finalny `.npz` zbudowany po `UC-19` zasila trening.

## 22) Inne istotne reguly
- Trzymac sie istniejacych kontraktow i nazw typow z poprzednich historyjek.
- `FE` ma respektowac kolejnosc z backendu.
- `FE` ma pozostac cienki:
  - backend zwraca liste,
  - `ViewController` steruje stanem,
  - `Model` pilnuje draftow,
  - `View` renderuje.
- Lokalny model `UC-19` moze byc inny niz `UC-18`, bo obsluguje inna semantyke biznesowa.
- Generycznosc ma dotyczyc przede wszystkim:
  - klienta HTTP,
  - helpera transportowego,
  - ewentualnych czystych helperow splitow,
  - a nie wymuszonego reuse calego ekranu `UC-18`.
- Ten endpoint ma pozostac krokiem konfiguracji, a nie miejscem realizacji calego builda `.npz`.

## 23) Plan weryfikacji minimum
- `npm run check`
- `npm run build`
- scenariusz happy path:
  - poprawny `preparationName`,
  - backend zwraca `type = "board"`,
  - lista folderow renderuje sie poprawnie,
  - operator moze zaznaczyc zrodla i ustawic splity.
- scenariusz pustej listy:
  - `200 OK`,
  - UI pokazuje pusty stan bez bledu.
- scenariusz `401`:
  - `onUnauthorized` zostaje wywolane.
- scenariusz `404`:
  - UI pokazuje blad stalego preparation,
  - krok builda zostaje zablokowany.
- scenariusz niepoprawnego `type`:
  - odpowiedz jest traktowana jako blad kontraktowy.
- scenariusz odswiezenia:
  - zrodla nadal istniejace zachowuja zaznaczenie i splity,
  - zrodla usuniete z backendu sa zdejmowane z lokalnego draftu.
- scenariusz walidacji splitow:
  - `mix` nie laczy sie z `train/val/test`,
  - aktywne zrodlo bez splitu jest traktowane jako niepoprawne.

## 24) Podsumowanie decyzji
- Dla `GET /api/datasets/preparations/{preparationName}/board/folders` w `UC-19` reuse'ujemy:
  - kontrakt,
  - klient HTTP,
  - helper transportowy,
  - ogolne wzorce requestu i logowania.
- Nie reuse'ujemy 1:1 calego `UC-18`-owego widoku ani hooka, bo maja inna semantyke biznesowa.
- Najwazniejsze granice odpowiedzialnosci:
  - `Infrastructure` pobiera i waliduje kontrakt,
  - `ViewController` utrzymuje liste i drafty builda,
  - `Model` pilnuje zgodnosci splitow,
  - `View` tylko renderuje i deleguje akcje.
- Najwazniejsze guardraile:
  - brak duplikacji klienta,
  - brak mieszania z browse/delete `UC-18`,
  - brak zgadywania danych po stronie FE,
  - brak eager-loadu `board/files`,
  - brak ciezkiego logowania.
