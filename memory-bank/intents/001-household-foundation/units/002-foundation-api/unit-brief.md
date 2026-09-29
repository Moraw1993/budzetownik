---
unit: 002-foundation-api
intent: 001-household-foundation
unit_type: backend
default_bolt_type: ddd-construction-bolt
phase: inception
status: complete
created: '2026-09-09T22:26:09.504Z'
updated: '2026-09-09T22:26:09.504Z'
---
# Domeny fundamentu w Django

## Cel i zakres
Reguły domenowe i API: konta, role, izolacja, zaproszenia, członkowie, dochody i audyt. Jeden proces backendu, jedna baza PostgreSQL. Bez budżetów i transakcji finansowych kolejnych MVP.

## Przypisane wymagania
FR-01, FR-02, FR-03, FR-04, FR-05, FR-06, FR-07, FR-08, FR-09, NFR-01, NFR-03.


## Encje i granice
User; Household; HouseholdUser; Invitation; HouseholdMember; RelationshipType; IncomeSource; AuditLog. Podział wewnętrzny: auth, households, members, income, audit.
Interfejsy między frontendem i backendem będą określone przed implementacją UI; protokół HTTP/JSON z lokalnym HTTPS.
Logika i autoryzacja w Django; PostgreSQL i Django ORM; dane dziesiętne.
Nie dodawać wymagań z MVP 2–5 do tego etapu.

## Zależności
001-local-runtime

## Stories
Łącznie 13, wszystkie Must, status draft.
- [001-bootstrap-account](stories/001-bootstrap-account.md): Pierwsze konto.
- [002-session-login](stories/002-session-login.md): Logowanie i wylogowanie.
- [003-local-recovery](stories/003-local-recovery.md): Lokalne odzyskiwanie dostępu.
- [004-create-household](stories/004-create-household.md): Tworzenie gospodarstwa.
- [005-household-roles](stories/005-household-roles.md): Role i ochrona właściciela.
- [006-tenant-isolation](stories/006-tenant-isolation.md): Izolacja i wybór gospodarstwa.
- [007-issue-invitation](stories/007-issue-invitation.md): Wydanie i odwołanie zaproszenia.
- [008-accept-invitation](stories/008-accept-invitation.md): Przyjęcie zaproszenia.
- [009-household-members](stories/009-household-members.md): Członkowie niezależni od kont.
- [010-family-relations](stories/010-family-relations.md): Konfigurowalne relacje rodzinne.
- [011-income-sources](stories/011-income-sources.md): Źródła dochodu.
- [012-financial-audit](stories/012-financial-audit.md): Audyt zmian.
- [013-preserve-history](stories/013-preserve-history.md): Dezaktywacja bez utraty historii.

## Plan realizacji
- 002-foundation-api: Konta, sesje i odzyskanie dostępu.
- 003-foundation-api: Gospodarstwa, role i izolacja.
- 004-foundation-api: Zaproszenia bez e-maili.
- 005-foundation-api: Członkowie, dochody i audyt.

## Kryteria sukcesu
- Wszystkie kryteria stories zweryfikowane rzeczywistymi wynikami.
- Brak zmiany uzgodnionej macierzy uprawnień i zakresu.
- Błędy i limity testów jawnie opisane, bez deklarowania wykonania planowanych testów.
