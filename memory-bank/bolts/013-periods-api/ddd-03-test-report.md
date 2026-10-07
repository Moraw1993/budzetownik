---
unit: 001-periods-api
bolt: 013-periods-api
stage: test
status: complete
updated: '2026-10-07T17:37:46Z'
---

# Raport testów: API okresów rozliczeniowych

## Wynik

- Pełny zestaw Django na PostgreSQL: **95/95 testów zaliczonych**.
- Pełny zestaw pod `coverage.py 7.16.2`: **95/95 testów zaliczonych**.
- Pokrycie produkcyjnego pakietu `households`, bez testów i migracji: **97% pokrycia instrukcji (991 instrukcji, 26 niepokrytych)**. To nie jest pokrycie gałęziowe ani całego backendu.
- `scripts/quality.ps1`: **PASS** po integracji repozytoryjnej polityki LF z PR #6 (`ec74b975ad02e9cd587ee65d15b6092b7685956e`): Ruff format/check, Prettier, ESLint, Stylelint i TypeScript.
- `python manage.py makemigrations --check --dry-run households`: **No changes detected**.
- Próba integracji z aktualnym `origin/develop` (`ec74b975ad02e9cd587ee65d15b6092b7685956e`): `git merge-tree --write-tree` zakończył się kodem 0.
- P95 endpointów okresów nie mierzono; pomiar pozostaje w zakresie acceptance bolta 017.

## Zakres i środowisko

Bolt 013 dodaje 9 testów: siedem testów API i dwa testy współbieżności. Obejmują one tworzenie roku z 12 miesiącami, walidację, role, izolację gospodarstw, niezależne przejścia miesięcy, audyt, rollback oraz równoległe tworzenie roku i aktywację miesiąca.

Testy uruchomiono w kontenerze backendu na testowej bazie PostgreSQL. Kontrola migracji użyła istniejącej bazy `postgres` tylko do odczytu. `coverage.py` zainstalowano wyłącznie w jednorazowym kontenerze pomiarowym; nie dodano zależności ani artefaktu coverage do repozytorium.

## Kryteria akceptacji

| Historia | Wynik |
| --- | --- |
| `001-create-year-months` | ✅ Rok tworzy dokładnie 12 miesięcy w transakcji, wszystkie początkowo nieaktywne. Testy sprawdzają duplikat, zakres, rok przestępny, atomowość, audyt i izolację gospodarstw. |
| `002-activate-month` | ✅ Jawna aktywacja jest niezależna od innych miesięcy; może być aktywnych kilka okresów. Testy sprawdzają ponowienie przejścia, role i audyt. |
| `003-close-and-reopen-month` | ✅ API okresów sprawdza przejścia i audyt. Integracja z zapisem przychodu jest pokryta w 014: testy PostgreSQL `test_close_first_rejects_create_patch_and_delete_after_waiting` i `test_write_first_commits_create_patch_and_delete_before_close` sprawdzają oba porządki blokad dla CREATE/PATCH/DELETE. Stage 5 bolta 014 uzyskał niezależne **ACCEPTED / PASS (8,8/10)**. |

## Bezpieczeństwo i współbieżność

Testy API okresów weryfikują wymagane role, odmowy dla ról bez zapisu, 404 dla zasobów innego gospodarstwa, pojedyncze zdarzenia audytu i rollback przy błędzie audytu. Testy współbieżności na PostgreSQL sprawdzają utworzenie jednego kompletnego roku oraz równoległe aktywacje bez niespójnego stanu i podwójnego audytu.

Testy integracyjne bolta 014 wykonują CREATE/PATCH/DELETE przy jednoczesnym zamykaniu miesiąca. W obu kierunkach testy obserwują, że konkurencyjny backend PostgreSQL czeka na blokadę, a końcowy stan i audyt odpowiadają kolejności serializowanych operacji. Nie twierdzą, że obserwacja `wait_event_type=Lock` izoluje konkretny wiersz blokady.

Podczas niezależnego review test słownika firm wykrył, że porównywał czas utworzenia umowy z czasem archiwizacji jako zastępczy dowód kolejności operacji. Zastąpiłem tę kruchą zależność od zegara ściennego bezpośrednim zapisem kolejności uzyskania wspólnej blokady; asercja teraz wymaga odrzucenia nowej umowy, gdy pierwsza blokadę uzyska archiwizacja, i dopuszcza ją, gdy pierwsza była umowa. Test przeszedł 8 kolejnych powtórzeń oraz pełny zestaw pod coverage (95/95).

## Pokrycie

Zakres: kod produkcyjny `households`, z wyłączeniem `*/tests/*` i `*/migrations/*`.

| Metryka | Wynik |
| --- | ---: |
| Instrukcje | 991 |
| Niepokryte instrukcje | 26 |
| Pokrycie instrukcji | 97% |

Wynik przekracza wymagane 80%. Nie jest to pokrycie gałęziowe; poprzedni raport błędnie opisywał metrykę jako branch coverage i podawał nieaktualne 99%.

## Bramki końcowe

- [x] Historie bolta 013 zweryfikowane, w tym zamknięty okres względem zapisów przychodu w integracyjnych testach 014.
- [x] Pokrycie kodu przekracza 80%.
- [x] Testy bezpieczeństwa przechodzą.
- [x] Kontrola jakości i migracji przechodzi.
- [x] Zależny bolt 014 ma zaakceptowany checkpoint Stage 5.
- [x] Formalne domknięcie metadanych bolta po akceptacji niezależnego review tego raportu.

P95 endpointów okresów pozostaje niezmierzony i przypisany do bolta akceptacyjnego 017; raport nie przedstawia tego pomiaru jako wykonanego.

## Checkpoint

Stage 5 uzyskał niezależne **ACCEPTED / PASS**. Oficjalny `bolt-complete.cjs` oznaczył bolt i trzy stories jako complete oraz zamknął jednostkę 001-periods-api. P95 tras okresów pozostaje zaplanowany do pomiaru w 017.
