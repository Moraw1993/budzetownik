---
id: 012-financial-audit
unit: 002-foundation-api
intent: 001-household-foundation
status: complete
priority: must
created: '2026-09-09T22:26:09.504Z'
assigned_bolt: 005-foundation-api
implemented: true
requirements:
  - FR-09
---
# Audyt zmian

## User Story
Jako Owner chcę mieć historię zmian źródeł, aby ustalić kto i co zmienił.

## Kryteria akceptacji
- [ ] Utworzenie, zmiana i dezaktywacja źródła zapisują wykonawcę, czas, obiekt, gospodarstwo i wartości przed/po w tej samej transakcji.
- [ ] Nieudana operacja nie tworzy zapisu o skutecznej zmianie; audyt nie zawiera haseł, ciasteczek ani tokenów zaproszeń.
- [ ] Zdarzenia logowania są rejestrowane niezależnie od wyboru gospodarstwa; zwykłe API nie umożliwia edycji audytu.

## Zależności
Bolty wymagane: 004-foundation-api.
W tym bolcie poprzedzają: 009-household-members, 010-family-relations, 011-income-sources.
Pełna identyfikacja story: 002-foundation-api/012-financial-audit.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
