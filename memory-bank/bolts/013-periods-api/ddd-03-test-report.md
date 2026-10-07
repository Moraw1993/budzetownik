---
unit: 001-periods-api
bolt: 013-periods-api
stage: test
status: awaiting-validation
updated: '2026-10-07T10:49:02Z'
---

# Raport testów: API okresów rozliczeniowych

## Podsumowanie

- Pełny zestaw Django (`households accounts runtime`): **91/91 testów przeszło** na testowej bazie PostgreSQL.
- Bolt 013 wnosi 8 testów: 6 testów API oraz 2 testy współbieżności. Obejmują one tworzenie pełnego roku, walidację, role, izolację gospodarstw, niezależne przejścia miesięcy, audyt, rollback oraz równoległe tworzenie roku i aktywację miesiąca.
- `scripts/quality.ps1` przeszła: Ruff, Prettier, ESLint, Stylelint i TypeScript. `makemigrations --check --dry-run` zwrócił `No changes detected`; migrację 0005 objęły pełne testy.
- Pokrycie gałęziowe zmienionych modułów aplikacyjnych wyniosło **99%** (385 instrukcji, 3 niepokryte, 16 gałęzi, 1 częściowo pokryta). Pomiar wykonałem w jednorazowym kontenerze; nie dodano zależności do projektu.
- Wydajności endpointów okresów nie zmierzono. Istniejący `scripts/acceptance_perf.py` nie obsługuje tych tras, więc cel P95 <500 ms pozostaje niezweryfikowany.

## Środowisko i metoda

Testy i pomiar pokrycia uruchomiłem w jednorazowych kontenerach backendu z odrębną testową bazą PostgreSQL. Nie migrowałem ani nie modyfikowałem bazy uruchomionej aplikacji. `coverage` został doinstalowany tylko w kontenerze pomiarowym.

Pełny zestaw Django uruchomiony pod coverage ponownie przeszedł 91/91 testów. Osobno uruchomiono też `scripts/quality.ps1` oraz `python manage.py makemigrations --check --dry-run` przed commitem implementacji; od tych kontroli nie zmieniał się kod.

## Kryteria akceptacji

| Historia | Wynik |
| --- | --- |
| `001-create-year-months` | ✅ Rok tworzy dokładnie 12 miesięcy, wszystkie nieaktywne; walidacja duplikatu i zakresu, atomowość, audyt i izolacja gospodarstw zweryfikowane. |
| `002-activate-month` | ✅ Jawna aktywacja jest niezależna; kilka miesięcy może być aktywnych, ponowienie przejścia jest deterministyczne, a role i audyt sprawdzone. |
| `003-close-and-reopen-month` | ⚠️ Zamknięcie i ponowne otwarcie, dozwolone przejścia, idempotencja, role i audyt są sprawdzone. Blokowanie zapisu przychodu oraz wyścig zapisu z zamknięciem wymagają testu integracyjnego z API przychodów z bolta 014; tego API jeszcze nie ma w zakresie bolta 013. |

## Testy API, bezpieczeństwa i współbieżności

Osiem testów bolta 013 sprawdza tworzenie roku z dwunastoma miesiącami (w tym długość lutego w roku przestępnym), odmowę duplikatu i niepoprawnych pól, listowanie, przejścia stanów, wymagane role, nieujawnianie obcych danych, pojedyncze wpisy audytu oraz wycofanie operacji przy błędzie audytu. Dwa testy współbieżności na PostgreSQL sprawdzają, że wyścig tworzenia kończy się jednym kompletnym rokiem, a równoległe aktywacje zachowują stan i nie duplikują audytu.

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

Brak pomiaru wynika z tego, że obecny benchmark akceptacyjny obejmuje gospodarstwa, członków i dawne źródła dochodu, ale nie endpointy okresów. Nie należy traktować tego raportu jako potwierdzenia celu wydajności dla nowych tras.

## Otwarte kwestie

| Kwestia | Waga | Status |
| --- | --- | --- |
| Integracyjna ochrona zamkniętego miesiąca przed zapisem przychodu, wraz z wyścigiem zamknięcie–zapis | Wysoka dla kompletności historii 003 | Do zweryfikowania w bolcie 014, gdy powstanie API przychodów |
| Pomiar P95 tras okresów | Niska | Do dodania do benchmarku akceptacyjnego przed oceną wydajności |

Nie znaleziono błędów krytycznych. Zgodnie z zakresem następny bolt 014 ma wykorzystać blokadę roku z ADR-006 przed zapisem przychodu; wtedy można zweryfikować powiązaną regułę historii 003 end-to-end.

## Checkpoint

Raport Stage 5 jest gotowy do przeglądu. Testy i pokrycie są zielone; nie oznaczam jednak całego bolta jako gotowego do Operations, ponieważ zachowanie zamkniętego miesiąca wobec zapisu przychodu czeka na integrację z boltem 014, a pomiar P95 nie został wykonany. Oczekuję na decyzję użytkownika przed formalnym zamknięciem Stage 5.

## Ready for Operations

- [ ] Wszystkie kryteria akceptacji bolta sprawdzone end-to-end — pozostaje integracja z API przychodów z bolta 014.
- [x] Pokrycie kodu >80%.
- [ ] Brak otwartych kwestii o wysokim wpływie na pełną historię — integracja ochrony przychodu czeka na bolt 014.
- [ ] Cel wydajności zweryfikowany.
- [x] Testy bezpieczeństwa przechodzą.
