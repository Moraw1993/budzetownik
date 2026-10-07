---
unit: 001-periods-api
bolt: 013-periods-api
stage: test
status: awaiting-validation
updated: '2026-10-07T11:21:40Z'
---

# Raport testów: API okresów rozliczeniowych

## Podsumowanie

- Pełny zestaw Django (`households accounts runtime`): **92/92 testów przeszło** na testowej bazie PostgreSQL.
- Bolt 013 wnosi 9 testów: 7 testów API oraz 2 testy współbieżności. Obejmują one tworzenie pełnego roku, walidację, role, izolację gospodarstw, wszystkie dziewięć kombinacji lifecycle, timestampy, audyt, rollback oraz wyścigi tworzenia roku i aktywacji.
- Ruff 0.16.6, ESLint, Stylelint i TypeScript przechodzą. `scripts/quality.ps1` nie przechodzi, ponieważ Prettier wskazuje 34 niezmienione pliki spoza zakresu kontraktu 013. `makemigrations --check --dry-run` zwrócił `No changes detected`; migrację 0005 objęły pełne testy.
- Pokrycie gałęziowe zmienionych modułów aplikacyjnych wyniosło **99%** (385 instrukcji, 3 niepokryte, 16 gałęzi, 1 częściowo pokryta). Pomiar wykonałem w jednorazowym kontenerze; nie dodano zależności do projektu.
- Wydajności endpointów okresów nie zmierzono. Istniejący `scripts/acceptance_perf.py` nie obsługuje tych tras, więc cel P95 <500 ms pozostaje niezweryfikowany.

## Środowisko i metoda

Testy i pomiar pokrycia uruchomiłem w jednorazowych kontenerach backendu z odrębną testową bazą PostgreSQL. Nie migrowałem ani nie modyfikowałem bazy uruchomionej aplikacji. `coverage` został doinstalowany tylko w kontenerze pomiarowym.

Pełny zestaw Django uruchomiony pod coverage podczas Stage 4 przeszedł 91/91 testów. Po dodaniu macierzy ponownie uruchomiono pełny backend i uzyskano 92/92. Coverage dotyczy kodu aplikacyjnego z commita implementacji `e9f582b`; nowa zmiana Stage B dotyczy wyłącznie testu. `scripts/quality.ps1` uruchomiono ponownie: Ruff przeszedł, ale Prettier zgłosił 34 zastane pliki. ESLint, Stylelint i TypeScript uruchomiono osobno i przeszły.

## Kryteria akceptacji

| Historia | Wynik |
| --- | --- |
| `001-create-year-months` | ✅ Rok tworzy dokładnie 12 miesięcy, wszystkie nieaktywne; walidacja duplikatu i zakresu, atomowość, audyt i izolacja gospodarstw zweryfikowane. |
| `002-activate-month` | ✅ Jawna aktywacja jest niezależna; kilka miesięcy może być aktywnych, ponowienie przejścia jest deterministyczne, a role i audyt sprawdzone. |
| `003-close-and-reopen-month` | ✅ Stan i lifecycle przechodzą pełną macierz 3×3; testy potwierdzają status HTTP, timestampy i audyt/no-op. Ochrona income CRUD przy close oraz wyścigi zapisu z zamknięciem zostały przeniesione do jawnych kryteriów 014 i pozostają do dowodu w tym bolcie. |

## Testy API, bezpieczeństwa i współbieżności

Siedem testów API bolta 013 sprawdza tworzenie roku z dwunastoma miesiącami (w tym długość lutego w roku przestępnym), odmowę duplikatu i niepoprawnych pól, listowanie, role, izolację gospodarstw, audyt oraz rollback. Test macierzy obejmuje każdą parę stan/operacja, sprawdzając odpowiedź, niezmienność lub zmianę timestampów i liczbę/treść audytu; potwierdza także `reopen(active)` jako no-op. Dwa testy współbieżności na PostgreSQL sprawdzają wyścig tworzenia roku i równoległe aktywacje.

Testy bezpieczeństwa są częścią testów API, a nie oddzielnie oznaczoną grupą: sprawdzono odmowę zapisu dla Member/Viewer oraz odpowiedź 404 dla zasobów innego gospodarstwa.

## Pokrycie

| Moduł | Pokrycie z gałęziami |
| --- | ---: |
| `households/exceptions.py` | 100% |
| `households/models.py` | 100% |
| `households/period_serializers.py` | 100% |
| `households/period_services.py` | 93% |
| `households/period_views.py` | 100% |
| `households/record_serializers.py` | 100% |
| `households/urls.py` | 100% |
| **Łącznie** | **99%** |

Zakres pomiaru obejmuje zmienione moduły wykonawcze, nie migrację ani testy. Niepokryte linie serwisu okresów dotyczą ścieżek konfliktu i błędu zapisu; główne zachowanie oraz wycofanie przy błędzie audytu mają testy.

## Wydajność

| Metryka | Cel | Wynik | Status |
| --- | --- | --- | --- |
| P95 endpointów okresów | <500 ms | Nie zmierzono | ⚠️ |
| Przepustowość | Nie określono | Nie zmierzono | — |

Brak pomiaru wynika z tego, że obecny benchmark akceptacyjny obejmuje gospodarstwa, członków i dawne źródła dochodu, ale nie endpointy okresów. Właścicielem benchmarku okresów i całego przepływu jest bolt 017; do jego wykonania P95 pozostaje niezweryfikowane.

## Otwarte kwestie

| Kwestia | Waga | Status |
| --- | --- | --- |
| Integracyjna ochrona zamkniętego miesiąca przed zapisem przychodu, wraz z wyścigiem zamknięcie–zapis | Wysoka dla kompletności historii 003 | Do zweryfikowania w bolcie 014, gdy powstanie API przychodów |
| Pomiar P95 tras okresów | Niska | Do dodania do benchmarku akceptacyjnego przed oceną wydajności |

Nie znaleziono błędów krytycznych. Zgodnie z zakresem następny bolt 014 ma wykorzystać blokadę roku z ADR-006 przed zapisem przychodu; wtedy można zweryfikować powiązaną regułę historii 003 end-to-end.

## Checkpoint

Raport Stage 5 i proponowany podział zakresu są gotowe do wspólnego checkpointu. Bolt 013 pozostaje `in-progress`; nie zamykam go na podstawie wcześniejszej prośby o odbiór. Pozostają: jawna akceptacja replanningu i raportu 013, dowód close–write w 014 oraz pomiar P95 w 017. Pełna kontrola jakości również pozostaje zablokowana na zastanym formatowaniu 34 plików.

## Ready for Operations

- [ ] Wszystkie kryteria akceptacji bolta sprawdzone end-to-end — pozostaje integracja z API przychodów z bolta 014.
- [x] Pokrycie kodu >80%.
- [ ] Brak otwartych kwestii o wysokim wpływie na pełną historię — integracja ochrony przychodu czeka na bolt 014.
- [ ] Cel wydajności zweryfikowany.
- [x] Testy bezpieczeństwa przechodzą.
