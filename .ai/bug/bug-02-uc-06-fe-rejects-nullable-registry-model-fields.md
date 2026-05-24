# BUG — FE odrzuca poprawną listę modeli z nullable fields

## Status
- Typ: błąd kontraktu runtime po stronie `Frontend`
- Obszar: `Frontend`
- Powiązane UC: `UC-06`, `UC-08`, `INF-08`
- Priorytet: średni, bo blokuje wybór modelu bazowego i start treningu w UI
- Status naprawy: poprawione w FE przez dopuszczenie pól nullable w typach i guardzie

## Problem
Ekran `UC-06` pobiera dane wyboru przez:
- `GET /api/models/registry`,
- `GET /api/datasets/processed`.

Backend zwraca poprawny kontrakt `RegistryModelsListApiResponse`, ale FE pokazuje błąd:

```text
Backend zwrócił niepoprawny kształt RegistryModelsListApiResponse.
```

W praktyce lista modeli nie ładuje się w formularzu startu treningu, mimo że odpowiedź HTTP `200 OK` ma poprawną strukturę i zawiera modele z `canStartTraining = true`.

## Objaw
Problem występuje, gdy lista rejestru zawiera modele bootstrap z `createdAtUtc = null`, na przykład:

```json
{
  "name": "cnn-baseline",
  "sourceType": "bootstrap",
  "sourceRunName": null,
  "parentModelName": null,
  "createdAtUtc": null,
  "canStartTraining": true,
  "canUseForInference": false
}
```

Dla modeli treningowych `createdAtUtc` zwykle jest tekstową datą, więc pierwsze elementy listy mogą wyglądać poprawnie. FE odrzuca jednak całą odpowiedź, bo `items.every(...)` kończy się błędem na pierwszym elemencie bootstrap z `createdAtUtc = null`.

## Przyczyna
Kontrakt `GET /api/models/registry` dopuszcza pola nullable:
- `trainingProfileName: string | null`,
- `augmentationProfileName: string | null`,
- `createdAtUtc: string | null`.

Implementacja FE błędnie wymagała dla tych pól zawsze `string` w:
- `src/Frontend/src/types/api.ts`,
- `src/Frontend/src/api/trainings.ts`.

Najbardziej widocznym przypadkiem był `createdAtUtc`, bo modele bootstrap z `init_bootstrap` nie muszą posiadać daty utworzenia i Backend poprawnie mapuje ją na `null`.

## Decyzja architektoniczna
Źródłem błędu jest FE, nie `Backend` ani `MachineLearning/init_bootstrap`.

Modele bootstrap mogą mieć:
- `sourceType = "bootstrap"`,
- `sourceRunName = null`,
- `createdAtUtc = null`,
- `canUseForInference = false`, jeśli są tylko bazą do treningu.

To pozostaje zgodne z kontraktem rejestru modeli i z rolą `init_bootstrap`.

## Rozwiązanie
FE powinien traktować pola nullable zgodnie z kontraktem:

```ts
trainingProfileName: string | null;
augmentationProfileName: string | null;
createdAtUtc: string | null;
```

Runtime guard `isRegistryModelListItemApiResponse` powinien akceptować zarówno `string`, jak i `null` dla tych pól.

## Kryteria akceptacji
- `GET /api/models/registry` z modelami bootstrap zawierającymi `createdAtUtc = null` ładuje się bez błędu w FE.
- Formularz `UC-06` pokazuje modele z `canStartTraining = true`.
- FE nadal odrzuca odpowiedzi z niepoprawnymi typami pól wymaganych, np. `items` inne niż tablica albo `canStartTraining` inne niż boolean.
- `npm run check` w `src/Frontend` przechodzi bez błędów TypeScript.

