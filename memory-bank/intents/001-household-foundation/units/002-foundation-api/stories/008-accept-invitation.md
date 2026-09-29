---
id: 008-accept-invitation
unit: 002-foundation-api
intent: 001-household-foundation
status: complete
priority: must
created: '2026-09-09T22:26:09.504Z'
assigned_bolt: 004-foundation-api
implemented: true
requirements:
  - FR-04
  - FR-03
  - NFR-03
---
# Przyjęcie zaproszenia

## User Story
Jako zaproszona osoba chcę przyjąć link, aby dołączyć do gospodarstwa.

## Kryteria akceptacji
- [ ] Osoba bez konta tworzy konto przez ważny link i otrzymuje przypisaną rolę; osoba z kontem loguje się i dołącza.
- [ ] Zużyty, odwołany lub wygasły link nie tworzy konta ani członkostwa; ważność jest sprawdzana również przy zatwierdzaniu formularza.
- [ ] Dwa równoczesne przyjęcia nie zużywają zaproszenia dwukrotnie; istniejące członkostwo nie jest dublowane ani nie zmienia roli przez ponowne przyjęcie.

## Zależności
Bolty wymagane: 003-foundation-api.
W tym bolcie poprzedzają: 007-issue-invitation.
Pełna identyfikacja story: 002-foundation-api/008-accept-invitation.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
