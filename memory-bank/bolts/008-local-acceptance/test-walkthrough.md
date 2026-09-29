---
stage: test
bolt: 008-local-acceptance
status: approved
created: 2026-09-23T21:07:10Z
validated: 2026-09-23T21:09:49Z
---

# Raport odbioru lokalnego fundamentu

## Wynik

- **Scenariusz odbioru:** sześć kroków wykonanych na pustej instalacji testowej. Założono pierwsze konto, dwa gospodarstwa, członka bez konta, po dwa źródła członka i gospodarstwa, zaproszono użytkownika Viewer, przełączono gospodarstwo, odtworzono kontenery i zalogowano się ponownie.
- **Role i izolacja:** Owner i Administrator zapisali dane. Member, Viewer i żądania bez sesji nie zapisały członka ani źródła dochodu. Dostęp do drugiego gospodarstwa i bezpośrednie identyfikatory obcych zasobów zostały odrzucone. Po odwołaniu członkostwa sesja Viewer utraciła dostęp; liczba rekordów po odmowach nie wzrosła.
- **Kopia i odtworzenie:** dump PostgreSQL, archiwum wolumenu `media_data` i konfigurację zapisano z izolowanej instalacji. Po odtworzeniu w drugim projekcie porównanie gospodarstw, członkostw, członków, źródeł dochodu, audytu i sumy kontrolnej pliku zakończyło się poprawnie. To samo porównanie przeszło po ponownym utworzeniu kontenerów źródła.
- **Wydajność:** 10/10 serii osiągnęło `P95 < 500 ms`, bez błędnych odpowiedzi. Najwyższy P95 wyniósł **59,05 ms** dla tworzenia źródła dochodu przy pięciu równoczesnych klientach.
- **Jakość:** 68/68 testów Django, 1/1 nowy test Playwright, produkcyjny build oraz `scripts/quality.ps1` przeszły.

## Środowisko i dane

- Izolowany przebieg `40bd4fa9`: osobne projekty Compose, wolumeny i porty HTTPS dla źródła oraz celu. Bieżąca instalacja użytkownika nie była użyta do tworzenia ani odtwarzania danych testowych.
- Host: Windows 11, 16 logicznych CPU. Docker Desktop 28.3.2 przydzielał 16 CPU i 16 727 080 960 bajtów pamięci. Nie zapisano obciążenia hosta w czasie pomiaru.
- Przed zakończonym pomiarem wydajności instalacja źródłowa miała 482 członków i 305 źródeł dochodu; po nim 922 członków i 745 źródeł. Wszystkie te rekordy są syntetyczne. Pierwsza, przerwana próba pomiaru pozostawiła część syntetycznych rekordów, dlatego zestaw początkowy był większy niż w pierwotnym planie.
- Kopia testowa zawierała dump bazy 58 027 bajtów, archiwum załączników 10 240 bajtów i konfigurację 251 bajtów. W pierwszym gospodarstwie punkt porównania obejmował 3 członkostwa, 2 członków, 5 źródeł i 5 wpisów audytu; w drugim odpowiednio 1, 1, 1 i 1. Piąte źródło pierwszego gospodarstwa dodał Administrator podczas kontroli roli.
- Po testach oba projekty odbiorowe zostały zatrzymane. Ich wolumeny i dowody w `.runtime/acceptance/40bd4fa9/` zachowano do przeglądu raportu.

## Pomiar API

Pomiar wykonano przez lokalne HTTPS z ponownie używanym połączeniem i uwierzytelnioną sesją. Każda operacja miała 20 żądań rozgrzewki i 200 zmierzonych odpowiedzi przy równoległości 1 oraz ponownie przy równoległości 5. P95 obliczono metodą najbliższej rangi z czasu żądania i odczytu odpowiedzi po stronie klienta. Seria spełnia cel wyłącznie przy braku błędów i P95 ściśle poniżej 500 ms.

| Operacja API | P95, 1 klient | P95, 5 klientów | Błędy |
|---|---:|---:|---:|
| Lista gospodarstw | 5,13 ms | 11,00 ms | 0 |
| Lista członków | 11,07 ms | 21,48 ms | 0 |
| Lista źródeł dochodu | 11,51 ms | 26,69 ms | 0 |
| Utworzenie członka | 12,61 ms | 29,33 ms | 0 |
| Utworzenie źródła dochodu | 16,76 ms | 59,05 ms | 0 |

Pełne liczby prób i warunki zapisano w `.runtime/acceptance/40bd4fa9/performance.json`. Pomiar opisuje tę lokalną instalację i wielkość danych; nie dowodzi wydajności na innych komputerach ani przy większym obciążeniu.

## Kryteria stories

- ✅ **001-end-to-end-acceptance:** sześć kroków, role, brak sesji, dwa gospodarstwa, odwołanie dostępu i obce identyfikatory sprawdzono przez rzeczywiste API. Test przeglądarkowy potwierdził odrębne listy członków i źródeł. Nie wykorzystano prywatnych arkuszy.
- ✅ **002-backup-restore:** instrukcja opisuje bazę, załączniki, konfigurację, bezpieczne odtworzenie i odzyskanie konta. Automatyczny przebieg odtworzył kopię do drugiego projektu i porównał dane oraz plik. Ponowne utworzenie kontenerów zachowało dane. Sama ręczna sekwencja poleceń z instrukcji operatora nie była wykonywana osobno.
- ✅ **003-api-performance:** zapisano sprzęt, rozmiar danych, rozgrzewkę, liczbę prób i równoległość. Wszystkie zmierzone operacje spełniły cel `P95 < 500 ms` w opisanych warunkach.

## Testy i dowody

- [x] `scripts/acceptance_flow.py` — scenariusz syntetyczny, role, izolacja, porównanie po restarcie i odtworzeniu.
- [x] `scripts/acceptance_stack.py` — oddzielne instalacje, kopia, odtworzenie i restart kontenerów.
- [x] `frontend/tests/acceptance.spec.ts` — rozdzielenie danych dwóch gospodarstw w przeglądarce; 1/1 test przeszedł.
- [x] `backend/accounts/tests.py`, `backend/households/tests/`, `backend/runtime/tests.py` — 68/68 istniejących testów Django przeszło w izolowanym projekcie, w tym integralność tworzenia gospodarstwa, kwoty dziesiętne i odmowy dostępu.
- [x] `scripts/quality.ps1` — Ruff, Prettier, ESLint, Stylelint i TypeScript bez błędów.
- [x] `.runtime/acceptance/40bd4fa9/fixture.json`, `backup/`, `performance.json` — lokalne dowody testowe z ignorowanego folderu.

## Problemy wykryte i poprawione

- Początkowy test Playwright szukał dokładnej nazwy źródła dochodu, podczas gdy nagłówek wiersza zawiera również kategorię. Widok pokazywał właściwe dane; poprawiono lokalizator testu i ponowiono próbę z wynikiem 1/1.
- Pierwsza próba wydajności uruchamiała logowanie dla kolejnych połączeń i w ostatniej serii osiągnęła limit bezpieczeństwa logowania (HTTP 429). Narzędzie zmieniono na jedną sesję i połączenia HTTPS używane ponownie. Wyzerowano licznik prób wyłącznie w syntetycznej instalacji; cały pomiar wykonano ponownie z wynikiem 10/10 bez błędów.

## Checkpoint

Użytkownik zatwierdził raport i końcowy etap testów. Bolt 008 jest gotowy do formalnego zamknięcia.
