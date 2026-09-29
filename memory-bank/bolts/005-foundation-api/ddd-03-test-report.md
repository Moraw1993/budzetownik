---
unit: 002-foundation-api
bolt: 005-foundation-api
stage: test
status: complete
updated: 2026-09-18T08:26:45+02:00
---

# Raport testów — członkowie, dochody i audyt

## Wynik

Pełna regresja Django na PostgreSQL 17: **68/68 testów zaliczonych**, 0 błędów,
0 pominiętych. Czas pod coverage: 6,717 s. Liczba obejmuje 51 wcześniejszych
testów i 17 dodanych w bolcie 005 (15 API/integralności oraz 2 współbieżności).
Kategorie funkcjonalna, bezpieczeństwa i integracyjna pokrywają się; nie są
sumowane jako osobne zestawy.

Testy wykonano na odrębnej bazie testowej tworzonej i usuwanej przez Django,
z bieżącym kodem montowanym do jednorazowego kontenera backendu.
Coverage 7.16.1 zainstalowano wyłącznie w `/tmp/bolt005-tools` tego kontenera.
Nie zmieniono zależności produkcyjnych.

## Kryteria akceptacji

| Story | Zweryfikowane zachowanie | Wynik |
| --- | --- | --- |
| 009 | Członek bez konta; edycja i odczyt według ról; konto tylko z tego gospodarstwa; unikalne przypisanie także przy współbieżności | PASS |
| 010 | Słownik gospodarstwa, przypisanie relacji, brak wpływu na role; dezaktywacja zachowuje istniejące powiązania; unikalna aktywna nazwa | PASS |
| 011 | Pola FR-08, opcjonalny właściciel, dokładne kwoty, waluta, edytowalna nazwa; izolacja również gdy użytkownik jest Ownerem obu gospodarstw | PASS |
| 012 | Wykonawca, czas, gospodarstwo, obiekt i stany przed/po; rollback przy awarii audytu; whitelisty; audyt tylko do odczytu dla Ownera | PASS |
| 013 | Dezaktywacja zachowuje źródła i audyt; ponowienie nie tworzy dodatkowych wpisów; brak publicznego trwałego usuwania | PASS |

Zdarzenia logowania pozostają obsługiwane przez istniejący moduł accounts,
niezależnie od wybranego gospodarstwa, i objęte pełną regresją. Przegląd
usług potwierdził, że zapis źródła nie tworzy przychodu miesięcznego ani
transakcji finansowej — moduły te nie należą do tego etapu.

## Scenariusze bezpieczeństwa i integralności

- Owner/Administrator zapisują dane, Member/Viewer odczytują.
- Anonimowy dostęp i zapisy bez CSRF są odrzucane.
- Obce identyfikatory członka, relacji i źródła nie przekraczają zakresu URL.
- Odebranie członkostwa blokuje istniejącą sesję w danym gospodarstwie.
- Nieprawidłowa data końcowa, kwota, waluta, częstotliwość i pola spoza
  kontraktu nie powodują zapisu danych ani audytu.
- Awaria audytu wycofuje utworzenie, edycję i dezaktywację źródła.
- Dwa równoległe przypisania tego samego konta tworzą jednego członka.
- Dwie równoległe zmiany źródła zachowują ciągłość stanów audytu przed/po.
- Listy są paginowane; rekordy archiwalne zachowują jawny status.

## Pokrycie

Pomiar obejmuje linie i gałęzie. Poniższe procenty są zaokrąglonym wynikiem
`coverage report`; testy i migracje wyłączono z zestawienia kodu produkcyjnego.

| Zakres | Pokrycie |
| --- | --- |
| households + common, bez testów i migracji | 96% |
| households/models.py | 100% |
| households/record_serializers.py | 100% |
| households/record_services.py | 98% |
| households/record_views.py | 100% |

Surowy pomiar: `.runtime/bolt005.coverage`; raport JSON:
`.runtime/bolt005-coverage.json` (zawiera również testy i migracje, więc jego
globalnej wartości nie należy mylić z powyższym zakresem).

## Kontrola jakości

`scripts/quality.ps1` zakończony powodzeniem: Ruff format/check, Prettier,
ESLint, Stylelint i TypeScript. Zmieniony plik testów sformatowano i przejrzano.
Nie zmieniano kodu produkcyjnego ani schematu w etapie testowym.

## Ograniczenia i status odbioru

- P95 < 500 ms: **nie zmierzono**. Pomiar całego lokalnego MVP jest zgodnie
  z projektem zaplanowany w bolcie 008. Ten raport nie potwierdza celu wydajnościowego.
- Testy przeglądarkowe formularzy tych funkcji wymagają UI z boltów 006–007.
- Niezmienialność audytu dotyczy publicznego API; administrator bazy może
  zmienić dane bezpośrednio, zgodnie z doprecyzowaniem projektu.
- Nie wykryto błędów blokujących kryteria funkcjonalne stories 009–013.
- Raport zatwierdzony przez użytkownika 2026-09-18T08:26:45+02:00.
  Skrypt `bolt-complete.cjs` zamknął bolt, pięć stories oraz jednostkę API.
