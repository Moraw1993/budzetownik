---
id: 006-tenant-isolation
unit: 002-foundation-api
intent: 001-household-foundation
status: complete
priority: must
created: '2026-09-09T22:26:09.504Z'
assigned_bolt: 003-foundation-api
implemented: true
requirements:
  - FR-03
  - NFR-01
  - NFR-03
---
# Izolacja i wybór gospodarstwa

## User Story
Jako użytkownik chcę przełączać swoje gospodarstwa, aby widzieć właściwe dane.

## Kryteria akceptacji
- [ ] Lista gospodarstw zawiera tylko członkostwa użytkownika; wybrane gospodarstwo określa zakres list i operacji.
- [ ] Bez członkostwa odczyt i zapis po ręcznie zmienionym identyfikatorze gospodarstwa lub zasobu są odrzucane bez danych i zmian.
- [ ] Po odebraniu członkostwa istniejąca sesja nie daje dalszego dostępu do gospodarstwa; rola z jednego gospodarstwa nie działa w innym.

## Zależności
Bolty wymagane: 002-foundation-api.
W tym bolcie poprzedzają: 004-create-household, 005-household-roles.
Pełna identyfikacja story: 002-foundation-api/006-tenant-isolation.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
