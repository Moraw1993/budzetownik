---
bolt: 014-monthly-income-api
created: 2026-10-07T12:16:28Z
status: accepted
superseded_by: null
---

# ADR-007: Trwała idempotencja tworzenia przychodu

## Context

Klient może ponowić żądanie utworzenia przychodu po utracie odpowiedzi, mimo że pierwsza transakcja została zatwierdzona. Bez trwałego rozpoznania ponowienia można zapisać drugi rzeczywisty przychód. Operacja zależy również od gospodarstwa, roku, miesiąca, odbiorcy i źródła; samo porównanie treści JSON nie rozpoznaje zmiany kontekstu URL.

## Decision

Każde żądanie `POST` tworzące przychód wymaga UUID w nagłówku `Idempotency-Key`. Klucz jest unikalny w zakresie gospodarstwa, aktora i operacji `income.create`. Wersjonowany fingerprint obejmuje kod operacji, kanoniczne identyfikatory roku i miesiąca oraz znormalizowane dane żądania. Znormalizowane wartości obejmują UUID, kwotę z dwiema cyframi po przecinku, datę ISO oraz odbiorcę gospodarstwa zapisany jako `null`; klucze obiektu są sortowane przed obliczeniem SHA-256.

W jednej transakcji zapisujemy przychód, wpis audytu i rekord idempotencji zawierający oryginalny status HTTP oraz treść odpowiedzi. Odpowiedź jest odtwarzana tylko wtedy, gdy zakres URL istnieje i bieżący użytkownik nadal ma dostęp oraz uprawnienie do zapisu. Dokładne ponowienie zwraca pierwotny wynik również po zamknięciu miesiąca lub archiwizacji słownika; ponowne użycie tego samego klucza z innym zakresem albo ładunkiem zwraca `409 idempotency_conflict`.

W bazie obowiązuje unikalność `(household, actor, operation, client_key)`. Rekord klucza nie wygasa czasowo i pozostaje zachowany wraz z przychodem, także po jego miękkim usunięciu. Konflikt unikalności poza zwykłą serializacją przez blokadę gospodarstwa wycofuje całą zewnętrzną transakcję; nie wolno zatwierdzić przychodu lub audytu bez odpowiadającego im klucza.

Idempotencja dotyczy wyłącznie tworzenia. Edycja używa `expected_version`, a usunięcie jest miękkie i audytowane.

## Rationale

Wynik operacji i klucz są zatwierdzane atomowo, więc retry nie może utworzyć drugiego przychodu ani drugiego wpisu audytu. Włączenie identyfikatorów roku i miesiąca wiąże wynik z pełnym kontekstem operacji. Ponowne sprawdzenie dostępu zapobiega ujawnieniu zapisanego wyniku po cofnięciu uprawnień, a zachowanie klucza eliminuje ryzyko, że stary retry po wygaśnięciu okresu retencji utworzy nowy wpis.

### Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
| --- | --- | --- | --- |
| Polegać wyłącznie na ponowieniu po stronie klienta | Brak tabeli i dodatkowego kontraktu | Utracona odpowiedź może doprowadzić do drugiego wpisu finansowego | Nie zapewnia bezpieczeństwa retry |
| Ograniczyć unikalność do gospodarstwa i klucza | Prostszy zakres klucza | Użytkownicy gospodarstwa mogą wejść sobie w drogę, a klucz nie opisuje aktora ani operacji | Kontrakt wiąże retry z aktorem i `income.create` |
| Fingerprintować tylko treść żądania | Mniej danych w fingerprint | Ten sam payload może zwrócić wynik z innego roku lub miesiąca | Fingerprint obejmuje pełną tożsamość żądania |
| Usuwać stare klucze po TTL | Ograniczony rozmiar tabeli | Po TTL identyczny retry może zapisać duplikat historycznego przychodu | Klucze zachowujemy co najmniej przez cały czas istnienia rekordu; bez TTL |

## Consequences

### Positive

- Utracona odpowiedź i ponowione żądanie nie powodują podwójnego przychodu ani audytu.
- Zmieniony URL lub payload nie może odtworzyć wyniku innej operacji.
- Granica transakcji jednoznacznie wyklucza częściowy zapis przychodu, audytu i klucza.

### Negative

- Powstaje dodatkowy model, unikalny indeks i stały koszt przechowywania rekordów idempotencji.
- Klienci tworzący przychód muszą generować i zachowywać UUID klucza dla retry tej samej operacji.

### Risks

- Niespójna kanonikalizacja po zmianie wersji fingerprintu mogłaby błędnie odrzucić retry. Wersjonowanie algorytmu, testy kanonikalizacji oraz przechowywanie fingerprintu razem z wynikiem pozwalają zachować zgodność.
- Odpowiedź replay może zawierać reprezentację przychodu, który później usunięto miękko. Jest to zamierzony pierwotny wynik tej samej operacji; zwykły późniejszy odczyt zasobu nadal zwraca `404`.

## Related

- **Stories**: 001-record-income, 003-record-amount-currency-date.
- **Standards**: `memory-bank/standards/coding-standards.md`.
- **Previous ADRs**: ADR-002, ADR-004, ADR-006.
