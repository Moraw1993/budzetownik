---
id: 005-household-roles
unit: 002-foundation-api
intent: 001-household-foundation
status: complete
priority: must
created: '2026-09-09T22:26:09.504Z'
assigned_bolt: 003-foundation-api
implemented: true
requirements:
  - FR-05
  - NFR-01
---
# Role i ochrona właściciela

## User Story
Jako Owner chcę zarządzać rolami, aby delegować dostęp.

## Kryteria akceptacji
- [ ] Owner zmienia role; Administrator, Member i Viewer nie mogą zmieniać ról ani zarządzać zaproszeniami przez API.
- [ ] Owner i Administrator edytują członków i źródła; Member i Viewer tylko odczytują te zasoby.
- [ ] Usunięcie lub degradacja ostatniego Owner jest odrzucane, również przy współbieżnych żądaniach; przekazanie własności zachowuje przynajmniej jednego Owner i nie usuwa kont.

## Zależności
Bolty wymagane: 002-foundation-api.
W tym bolcie poprzedzają: 004-create-household.
Pełna identyfikacja story: 002-foundation-api/005-household-roles.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
