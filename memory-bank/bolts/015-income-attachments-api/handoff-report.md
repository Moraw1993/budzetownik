---
bolt: 015-income-attachments-api
created: '2026-10-08T20:18:26Z'
status: complete
---

# Raport przekazania — okresy, przychody i załączniki

Bolt 015 oraz jednostka `002-monthly-income-api` są ukończone. Reviewer zaakceptował Stage 5 i ADR-009: **8,9/10 — ACCEPTED / PASS**, dla kodu `2a4dda2a51c4ca7fe887a823e21e32446ae16da4`. Oficjalny `bolt-complete.cjs` zakończył bolta, story 005 i jednostkę API; pozostałe jednostki UI/odbioru są nadal zaplanowane.

## Wykonane podczas tego ciągu pracy

**Bolt 014 — API rzeczywistych przychodów:** ukończony wcześniej, zaakceptowany po review i scalony przez PR #8. Obsługuje wpisy dla osoby lub gospodarstwa, słownikowe źródła, kwotę/walutę/datę otrzymania oraz sumy miesiąca/roku według waluty. Utworzenie ma trwałą idempotencję, dane historyczne mają snapshoty, usunięcie jest logiczne, a mutacje i audit są atomowe. Zapisy wymagają aktywnego miesiąca.

**Bolt 015 — prywatne załączniki:** upload, lista, autoryzowany download i usunięcie PNG, JPG/JPEG i PDF. Wieloplikowy zapis udostępnia wszystkie metadata i audit atomowo. Pliki trafiają do trwałego prywatnego storage przez zablokowany zapis wstępny i promotion; usunięcie oraz reconciliation mają powtarzalne sprzątanie. Limity: 1–5 plików/request, 10 MiB/plik, 25 MiB/batch, 20 aktywnych plików i 50 MiB na przychód; proxy ogranicza body do 26 MiB.

**Naprawy po review:** zabezpieczono zatwierdzone bajty przed błędem finalizacji po commit, poprawiono postęp i integralność reconciliation oraz wyścig z legalnym usunięciem, wzmocniono walidację JPEG, role/tenant/404 matrix i deterministyczne testy rzeczywistych blokad PostgreSQL/OS. Upload pozostaje możliwy tylko w aktywnym miesiącu; uprawniony odczyt działa także dla zamkniętych/nieaktywnych okresów.

**Proxy i dowody:** baseline Caddy odtworzył fałszywe puste `200` po read deadline. Po konsultacji z doradcą API stosuje write deadline przed read deadline, dodatnie 10 min, zachowany limit 26 MiB oraz jawne h1/h2. Frontend nie dostał handler write budget. Utrwalono ADR-009 i opis późnego zapisu: brak odpowiedzi po pełnym body może oznaczać zatwierdzony upload, więc nie ma automatycznego retry. Manifest/assessor odrzuca niepełne, zduplikowane i uszkodzone dowody.

## Weryfikacja

| Dowód | Wynik |
| --- | --- |
| Pełna suite Django na PostgreSQL | 169/169 |
| Testy załączników wewnątrz suite | 39 |
| Statement coverage siedmiu nowych modułów produkcyjnych | 83%; reconciliation command 73% jest jawnie uwzględniony |
| Self-tests assessora dowodów | 10/10 |
| Finalny autorski TLS manifest H1/H2 | 133/133, zero evidence errors |
| Niezależny nowy TLS smoke reviewera | 25/25; dodatkowo ponowna ocena kopii archiwum 133 |
| Quality, migracje i Caddy validate/adapt | PASS |
| Końcowy reviewer | 8,9/10 — ACCEPTED / PASS |

Szczegóły i komendy: [raport testów](ddd-03-test-report.md). Polityka deadline’ów: [ADR-009](adr-009-proxy-upload-deadlines.md). Historia: [construction log](../../intents/003-budget-periods-and-income/units/002-monthly-income-api/construction-log.md).

## Stan przekazania

Kod jest na `feat/bolt-015-income-attachments-api` w worktree `C:/Users/Arek/.codex/worktrees/bolt-014-monthly-income-api/MyHomeBudget`. Commit kodu do review: `2a4dda2`; końcowy commit dokumentuje formalne domknięcie. Indeks scenariuszy odzwierciedla 48 źródłowych stories: 41 complete i 7 zaplanowanych. Dowody runtime są zachowane w ignorowanym `.runtime`, a kontenery probe zostały posprzątane.

Następne planowane prace to **016 — UI okresów/przychodów** (z obowiązkową bramką projektu i niezależnej oceny przed kodem) oraz **017 — odbiór end-to-end i P95**. Integracja brancha 015 do develop jest osobnym krokiem; w tym domknięciu nie wykonano release ani restartu aplikacji. Praca kończy się na przekazaniu tego zadania.
