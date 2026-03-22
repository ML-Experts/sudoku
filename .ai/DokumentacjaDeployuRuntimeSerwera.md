# Dokumentacja deployu i runtime serwera `sudoku`

## Cel dokumentu

Ten dokument opisuje docelowy model runtime, deployu i konfiguracji dla aplikacji `sudoku` działającej na serwerze Ubuntu 24.04.

Ma służyć jako źródło prawdy dla:

* workflow GitHub Actions / CI/CD,
* asystentów IDE takich jak Cursor,
* skryptów deployowych,
* osób wdrażających kolejne wersje FE / BE / ML.

---

# 1. Architektura systemu

Aplikacja jest podzielona na 3 warstwy:

* **FE** — frontend, publicznie dostępny przez nginx
* **BE** — backend C# / .NET 10, publiczne API dostępne tylko przez nginx
* **ML** — wewnętrzna usługa Python / FastAPI, niewystawiona do internetu

## Zasady komunikacji

Dozwolona komunikacja:

* **Przeglądarka użytkownika -> nginx -> FE**
* **Przeglądarka użytkownika -> nginx -> BE** przez ścieżkę `/api/...`
* **BE -> ML** po `http://127.0.0.1:8000`

Niedozwolona komunikacja:

* **FE -> ML** bezpośrednio
* **Internet -> ML** bezpośrednio
* **Internet -> BE** z pominięciem nginx

## Publiczne porty

Na zewnątrz mają być wystawione tylko:

* `80/tcp`
* `443/tcp`
* `22/tcp` dla SSH

Porty wewnętrzne:

* BE: `127.0.0.1:5000`
* ML: `127.0.0.1:8000`

Oznacza to, że backend i ML słuchają tylko na localhost i nie są bezpośrednio osiągalne z internetu.

---

# 2. Layout systemu plików na serwerze

## Główne katalogi

```text
/opt/sudoku/
├── backend/                   # aktywna wersja backendu
├── ml/                        # aktywna wersja ML
├── releases/
│   ├── backend/               # wrzutnia release'ów backendu
│   ├── ml/                    # wrzutnia release'ów ML
│   └── fe/                    # wrzutnia release'ów frontendu
├── shared/
│   ├── data/
│   │   ├── raw/
│   │   ├── processed/
│   │   └── benchmark/
│   ├── models/
│   │   ├── active/
│   │   └── registry/
│   ├── trainings/
│   │   ├── runs/
│   │   ├── reports/
│   │   └── metadata/
│   ├── examples/
│   │   ├── uploads/
│   │   └── generated/
│   └── tmp/
└── scripts/                   # skrypty deployowe

/var/www/sudoku/fe             # aktywny frontend serwowany przez nginx
/etc/sudoku/                   # miejsce na systemowe dodatki / przyszłe override'y
/var/log/sudoku/               # logi aplikacyjne jeśli używane poza journald
```

## Znaczenie katalogów

### `/opt/sudoku/backend`

Zawiera **aktywną, uruchamianą wersję backendu**.

To tutaj po deployu znajdują się pliki z `dotnet publish`, np.:

* `*.dll`
* `appsettings.json`
* `appsettings.Production.json`
* inne artefakty publish

### `/opt/sudoku/ml`

Zawiera **aktywną, uruchamianą wersję warstwy ML**.

To tutaj po deployu znajdują się m.in.:

* kod FastAPI
* `.env`
* `requirements.txt`
* `.venv` utworzone na serwerze

### `/opt/sudoku/releases/...`

To są **katalogi wrzutni release'ów**. Użytkownik `cd` ma tam uploadować artefakty z CI/CD.

Release'y nie są uruchamiane bezpośrednio z `releases/`. Najpierw są promowane do katalogów aktywnych:

* `/opt/sudoku/backend`
* `/opt/sudoku/ml`
* `/var/www/sudoku/fe`

### `/opt/sudoku/shared/...`

To są dane współdzielone lub techniczne runtime.

Przykłady:

* modele aktywne i archiwalne
* dane treningowe
* uploady użytkowników
* artefakty generowane przez preprocess
* pliki tymczasowe

### `/opt/sudoku/scripts`

Skrypty deployowe uruchamiane przez ograniczone sudo użytkownika `cd`.

### `/var/www/sudoku/fe`

Aktywny frontend serwowany przez nginx.

To katalog z gotowym buildem statycznym. Powinien zawierać bezpośrednio np.:

* `index.html`
* `assets/...`

Nie powinno tam być źródeł projektu FE ani narzędzi buildowych.

---

# 3. Użytkownicy i grupy

## Użytkownicy

* `cd` — użytkownik do uploadu release'ów i wywoływania skryptów deployowych
* `sudoku-be` — użytkownik uruchamiający backend
* `sudoku-ml` — użytkownik uruchamiający ML
* `www-data` — nginx

## Grupy

* `sudoku-deploy` — grupa związana z release'ami i deployem
* `sudoku-shared` — grupa dla danych współdzielonych

## Zasady dostępu

### `cd`

Może:

* wrzucać pliki do `/opt/sudoku/releases/...`
* uruchamiać tylko wybrane skrypty deployowe przez `sudo`

Nie powinien:

* mieć pełnego sudo
* mieć bezpośredniego swobodnego zapisu do `/opt/sudoku/backend`
* mieć bezpośredniego swobodnego zapisu do `/opt/sudoku/ml`
* mieć bezpośredniego swobodnego zapisu do `/var/www/sudoku/fe`

### `sudoku-be`

Ma uruchamiać backend i mieć dostęp do swoich katalogów runtime oraz do wybranych katalogów `shared`.

### `sudoku-ml`

Ma uruchamiać ML, posiadać `.venv`, instalować zależności Pythona i mieć dostęp do swoich katalogów runtime oraz do wybranych katalogów `shared`.

---

# 4. Konfiguracja aplikacji

## Ogólna zasada

Konfiguracja runtime **jest dostarczana razem z deployem**.

Nie zakładamy, że administrator ręcznie tworzy produkcyjne `appsettings.json` albo `.env` na serwerze.

Sekrety i wartości środowiskowe powinny być podstawiane przez workflow CI/CD do artefaktów release.

## Backend (.NET 10)

Backend używa naturalnego dla .NET modelu konfiguracji:

* `appsettings.json`
* `appsettings.Production.json`
* ewentualnych innych wariantów środowiskowych, jeśli workflow je generuje

Te pliki:

* są częścią release'u backendu,
* po deployu leżą w `/opt/sudoku/backend/`.

### Co oznacza to dla workflow

Workflow backendu musi:

* wygenerować lub przygotować właściwe `appsettings*.json` dla środowiska,
* spakować je razem z artefaktami `dotnet publish`.

## ML (Python / FastAPI)

Warstwa ML używa:

* `api/.env`
* `requirements.txt`

Te pliki:

* są częścią release'u ML,
* po deployu leżą w `/opt/sudoku/ml/`.

### Co oznacza to dla workflow

Workflow ML musi:

* przygotować właściwy `api/.env` dla środowiska,
* dostarczyć `requirements.txt`,
* spakować kod aplikacji razem z `api/.env*` i `requirements.txt`.

## `/etc/sudoku`

Ten katalog nie jest obecnie głównym miejscem podstawowej konfiguracji runtime dla BE i ML.

Może być używany na:

* dodatki systemowe,
* przyszłe override'y,
* fragmenty configu nginx,
* inne elementy systemowe.

Nie należy zakładać, że CI/CD musi tam kopiować podstawowe `appsettings.json` lub `.env`.

---

# 5. Model deployu

## Ogólny model

Deploy ma być **release-based**.

To oznacza:

1. workflow buduje artefakt,
2. artefakt trafia do katalogu `releases`,
3. użytkownik `cd` lub workflow uruchamia odpowiedni skrypt deployowy,
4. skrypt promuje release do katalogu aktywnego,
5. usługa jest restartowana.

Nie budujemy aplikacji produkcyjnej bezpośrednio na serwerze, poza instalacją zależności Python dla ML.

---

# 6. Deploy FE

## Założenia

Frontend jest budowany w CI/CD.

Na serwer trafia gotowy build statyczny, np. zawartość `dist/` lub `build/`.

## Co workflow FE ma zrobić

* zainstalować zależności frontendu,
* wykonać build,
* spakować wynik builda do archiwum `.tar.gz`,
* przesłać archiwum do `/opt/sudoku/releases/fe/`.

## Co powinno być w release FE

Po rozpakowaniu katalog powinien zawierać bezpośrednio pliki serwowane przez nginx, np.:

```text
index.html
assets/...
```

Nie powinno być dodatkowego poziomu typu `dist/index.html` w środku archiwum, jeśli deploy script kopiuje zawartość 1:1 do `/var/www/sudoku/fe`.

## Co robi deploy FE

Skrypt deployu FE:

* znajduje najnowsze archiwum w `/opt/sudoku/releases/fe`,
* rozpakowuje je tymczasowo,
* kopiuje wynik do `/var/www/sudoku/fe`,
* ustawia ownera i prawa,
* nie wymaga restartu osobnej usługi aplikacyjnej.

---

# 7. Deploy BE

## Technologia

* C#
* .NET 10

## Założenia

Serwer **nie kompiluje backendu**.

Na serwerze ma być tylko odpowiedni **ASP.NET Core Runtime 9**.

## Co workflow BE ma zrobić

* `dotnet restore`
* `dotnet build`
* testy
* `dotnet publish -c Release`
* podstawić właściwe `appsettings*.json`
* spakować katalog publish do `.tar.gz`
* przesłać archiwum do `/opt/sudoku/releases/backend/`

## Co powinno być w release BE

Po rozpakowaniu powinny się tam znajdować pliki gotowe do uruchomienia przez `dotnet`, np.:

* `<NAZWA_DLL>.dll`
* `appsettings.json`
* `appsettings.Production.json`
* inne pliki publish

## Co robi deploy BE

Skrypt deployu backendu:

* znajduje najnowsze archiwum w `/opt/sudoku/releases/backend`,
* rozpakowuje je tymczasowo,
* kopiuje wynik do `/opt/sudoku/backend`,
* ustawia ownera i prawa,
* restartuje `sudoku-backend.service`.

## Ważne

W `systemd` trzeba wskazać rzeczywistą nazwę pliku DLL wygenerowanego przez publish.

Przykład:

```text
ExecStart=/usr/bin/dotnet /opt/sudoku/backend/<NAZWA_DLL>.dll
```

Nazwy katalogów i usługi nie muszą być identyczne z nazwą DLL, ale całość musi być spójna.

---

# 8. Deploy ML

## Technologia

* Python
* FastAPI
* uvicorn

## Ustalony model zależności

Dla ML przyjmujemy:

* release dostarcza kod,
* release dostarcza `.env`,
* release dostarcza `requirements.txt`,
* serwer tworzy / utrzymuje `.venv`,
* serwer instaluje zależności przez `pip install -r requirements.txt`.

Nie pakujemy `.venv` w release.

## Domyślna wersja Pythona

Na start produkcyjny przyjmujemy **Python 3.12** jako bezpieczny wybór operacyjny dla Ubuntu 24.04.

Jeśli później konkretne biblioteki ML zostaną świadomie przetestowane i zaakceptowane na Python 3.14, można zmienić wersję interpretera tylko dla warstwy ML.

## Co workflow ML ma zrobić

* przygotować kod aplikacji,
* podstawić właściwy `api/.env`,
* dołączyć `requirements.txt`,
* spakować release do `.tar.gz`,
* przesłać archiwum do `/opt/sudoku/releases/ml/`.

## Co powinno być w release ML

Przykładowy layout po rozpakowaniu:

```text
api/
application/
infrastructure/
models/
main.py
requirements.txt
```

lub inny, jeśli zgadza się z `ExecStart` i ścieżkami w systemd.

## Co robi deploy ML

Skrypt deployu ML:

* znajduje najnowsze archiwum w `/opt/sudoku/releases/ml`,
* rozpakowuje je tymczasowo,
* kopiuje wynik do `/opt/sudoku/ml`,
* ustawia ownera i prawa,
* jeśli `.venv` nie istnieje — tworzy je,
* wykonuje `pip install --upgrade pip`,
* wykonuje `pip install -r requirements.txt`,
* restartuje `sudoku-ml.service`.

## Dlaczego ten model

Ten model jest bardziej praktyczny niż pakowanie `.venv` do release, bo:

* unika problemów z binarną zgodnością środowiska build vs serwer,
* jest naturalny dla Pythona,
* pozwala łatwo aktualizować zależności,
* zachowuje prostotę release'u.

---

# 9. Usługi systemd

## Backend

Usługa backendu:

* działa jako `sudoku-be`,
* słucha na `127.0.0.1:5000`,
* jest restartowana po deployu,
* nie jest wystawiona publicznie.

## ML

Usługa ML:

* działa jako `sudoku-ml`,
* uruchamia uvicorn z `.venv`,
* słucha na `127.0.0.1:8000`,
* nie jest wystawiona publicznie,
* jest restartowana po deployu.

---

# 10. Nginx

## Rola nginx

Nginx jest publiczną bramą do systemu.

Odpowiada za:

* serwowanie FE z `/var/www/sudoku/fe`,
* terminację TLS,
* reverse proxy z `/api/...` do backendu.

## Zasady routingu

* `/` -> frontend
* `/api/` -> backend (`127.0.0.1:5000`)
* brak publicznego routingu do ML

## TLS

Na obecnym etapie można używać self-signed certyfikatu na `443`, aby mieć szyfrowanie dla środowiska testowego.

Docelowo certyfikat powinien zostać podmieniony na poprawny certyfikat domenowy.

---

# 11. Firewall i bezpieczeństwo sieciowe

Firewall ma wpuszczać tylko:

* `22/tcp`
* `80/tcp`
* `443/tcp`

Portów backendu i ML nie otwieramy, ponieważ są związane tylko z localhost.

## Fail2ban

Fail2ban ma być aktywny przynajmniej dla `sshd`.

## SSH

Rekomendacje:

* `PermitRootLogin no`
* klucze SSH zamiast haseł
* `PasswordAuthentication no` dopiero po potwierdzeniu poprawnego logowania kluczem

---

# 12. Odpowiedzialności workflow GitHub Actions / CD

## Workflow FE

Powinien:

* zbudować frontend,
* spakować gotowe pliki statyczne,
* przesłać archiwum do `/opt/sudoku/releases/fe/`,
* opcjonalnie uruchomić deploy FE.

## Workflow BE

Powinien:

* wykonać `dotnet publish` dla .NET 10,
* dostarczyć właściwe `appsettings*.json`,
* spakować wynik publish,
* przesłać archiwum do `/opt/sudoku/releases/backend/`,
* opcjonalnie uruchomić deploy BE.

## Workflow ML

Powinien:

* spakować kod,
* dołączyć `.env`,
* dołączyć `requirements.txt`,
* przesłać archiwum do `/opt/sudoku/releases/ml/`,
* opcjonalnie uruchomić deploy ML.

## Rekomendacja

Najbardziej praktyczny model to osobne workflow dla:

* `frontend`
* `backend`
* `ml`

Każda warstwa powinna móc być wdrażana niezależnie.

---

# 13. Ograniczone sudo dla `cd`

Użytkownik `cd` powinien mieć ograniczone sudo tylko do:

* `/opt/sudoku/scripts/deploy_backend.sh`
* `/opt/sudoku/scripts/deploy_ml.sh`
* `/opt/sudoku/scripts/deploy_fe.sh`
* restartów / statusów odpowiednich usług
* reloadu nginx

Nie powinien mieć pełnego `ALL=(ALL) ALL`.

---

# 14. Testy po deployu

## Test FE

* otwarcie `https://<host>`
* sprawdzenie, czy ładuje się `index.html`

## Test BE

* `curl -k https://<host>/api/ping`
* lub inny endpoint health/ping

## Test ML

* `curl http://127.0.0.1:8000/ml/ping`
* `curl http://127.0.0.1:8000/ml/health`

## Test end-to-end

Najlepiej mieć prosty ekran FE z przyciskiem wywołującym `/api/ping`.
To pozwala szybko potwierdzić drogę:

* FE -> nginx -> BE

Jeśli backend endpoint dodatkowo sprawdza ML, potwierdza też:

* BE -> ML

---

# 15. Najważniejsze założenia dla asystenta IDE / Cursor

Asystent generujący workflow, skrypty lub konfigurację ma przyjmować następujące zasady:

1. **Nie odwzorowujemy struktury repo 1:1 na serwerze.**
   Repo służy do developmentu, serwer do runtime i deployu.

2. **Release'y trafiają najpierw do `/opt/sudoku/releases/...`.**
   Dopiero potem są promowane do aktywnych katalogów.

3. **FE jest statyczny i serwowany przez nginx z `/var/www/sudoku/fe`.**

4. **Backend to .NET 10 uruchamiany z publish output w `/opt/sudoku/backend`.**

5. **ML to Python/FastAPI w `/opt/sudoku/ml`, z `.venv` utrzymywanym na serwerze i zależnościami instalowanymi z `requirements.txt`.**

6. **Konfiguracja runtime jest dostarczana przez workflow w release'ach.**
   Nie zakładamy ręcznej edycji `appsettings*.json` ani `.env` na serwerze jako podstawowego sposobu konfiguracji.

7. **ML nie może być publicznie routowany przez nginx.**

8. **BE i ML muszą słuchać tylko na localhost.**

9. **Użytkownik `cd` ma ograniczone sudo tylko do deployu i wybranych komend operacyjnych.**

10. **Workflow powinny być per warstwa i niezależne.**

---

# 16. Podsumowanie operacyjne

## FE

* build w CI/CD
* upload do `releases/fe`
* deploy do `/var/www/sudoku/fe`
* nginx serwuje statycznie

## BE

* `dotnet publish` w CI/CD
* `appsettings*.json` dostarczane w release
* upload do `releases/backend`
* deploy do `/opt/sudoku/backend`
* start przez `systemd`

## ML

* kod + `api/.env*` + `requirements.txt` w release
* upload do `releases/ml`
* deploy do `/opt/sudoku/ml`
* `.venv` i `pip install -r requirements.txt` na serwerze
* start przez `systemd`

Ten model należy traktować jako obowiązujący przy generowaniu workflow, skryptów i dokumentacji pomocniczej.
