---
total_decisions: 5
last_updated: 2026-09-23T21:30:14Z
---
# Decyzje architektoniczne

## ADR-001: Sesje Django i jawna ochrona CSRF
- Status: accepted.
- Bolt: 002-foundation-api.
- Dokument: [ADR](../bolts/002-foundation-api/adr-001-session-authentication.md).
- Czytać przy zmianach kont, sesji, walidacji API i limitów logowania.
- Decyzja: sesje Django, DRF, CSRF dla anonimowego logowania i konfiguracji, liczniki prób w PostgreSQL.

## ADR-002: Zakres gospodarstwa i blokada dostępu
- Status: accepted.
- Bolt: 003-foundation-api.
- Dokument: [ADR](../bolts/003-foundation-api/adr-002-household-access.md).
- Czytać przy implementacji członkostw, zaproszeń, danych gospodarstwa i zmian uprawnień.
- Decyzja: jawny identyfikator gospodarstwa w URL, aktualna rola z bazy, blokada agregatu i ponowna kontrola roli po oczekiwaniu.

## ADR-003: Ochrona tokenów zaproszeń
- Status: accepted.
- Bolt: 004-foundation-api.
- Dokument: [ADR](../bolts/004-foundation-api/adr-003-invitation-token-protection.md).
- Czytać przy implementacji lub zmianie zaproszeń, przyjęcia konta oraz logowania requestów zawierających sekrety.
- Decyzja: token jest w fragmencie lokalnego URL, w bazie pozostaje wyłącznie HMAC-SHA-256, a przyjęcie działa atomowo pod blokadą gospodarstwa i zaproszenia.

## ADR-004: Niezmienialny audyt zmian danych finansowych
- Status: accepted.
- Bolt: 005-foundation-api.
- Dokument: [ADR](../bolts/005-foundation-api/adr-004-immutable-financial-audit.md).
- Czytać przy implementacji zmian źródeł dochodu, budżetów, kredytów, oszczędności lub historii zmian.
- Decyzja: zmiana danych finansowych i zredagowany wpis audytu powstają w jednej transakcji; wpis audytu jest wyłącznie do odczytu.

## ADR-005: Wspólna tożsamość źródła dochodu dla umów i innych źródeł
- Status: accepted.
- Bolt: 010-family-income-api.
- Dokument: [ADR](../bolts/010-family-income-api/adr-005-shared-income-source-identity.md).
- Czytać przy zmianach modeli źródeł i umów, migracjach dawnych źródeł, projekcie przychodów miesięcznych oraz liście wyboru źródła.
- Decyzja: `IncomeSource` zachowuje wspólny UUID; `Contract` zawiera szczegóły 1:1, a migracja nie tworzy umów ani przychodów miesięcznych.
