---
id: 004-create-household
unit: 002-foundation-api
intent: 001-household-foundation
status: complete
priority: must
created: '2026-09-09T22:26:09.504Z'
assigned_bolt: 003-foundation-api
implemented: true
requirements:
  - FR-02
  - NFR-03
---
# Tworzenie gospodarstwa

## User Story
Jako użytkownik chcę utworzyć gospodarstwo, aby oddzielić finanse rodziny.

## Kryteria akceptacji
- [ ] Zalogowany użytkownik tworzy gospodarstwo z nazwą i walutą domyślną PLN i zostaje jego Owner.
- [ ] Gdy zapis członkostwa kończy się błędem, transakcja wycofuje utworzenie gospodarstwa.
- [ ] Utworzone gospodarstwo jest widoczne twórcy po ponownym zalogowaniu; można utworzyć więcej niż jedno.

## Zależności
Bolty wymagane: 002-foundation-api.
W tym bolcie poprzedzają: Brak.
Pełna identyfikacja story: 002-foundation-api/004-create-household.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
