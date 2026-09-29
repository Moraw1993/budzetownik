---
id: 001-bootstrap-account
unit: 002-foundation-api
intent: 001-household-foundation
status: complete
priority: must
created: '2026-09-09T22:26:09.504Z'
assigned_bolt: 002-foundation-api
implemented: true
requirements:
  - FR-01
---
# Pierwsze konto

## User Story
Jako operator chcę utworzyć pierwszego użytkownika, aby rozpocząć pracę.

## Kryteria akceptacji
- [x] Na pustej instalacji poprawna konfiguracja tworzy jedno konto i umożliwia logowanie; hasło nie jest zapisane jawnym tekstem.
- [x] Po utworzeniu pierwszego konta ten sam mechanizm odrzuca tworzenie kolejnych kont.
- [x] Dwa równoczesne żądania konfiguracji nie tworzą dwóch kont startowych; aplikacyjny użytkownik nie otrzymuje automatycznie uprawnień superuser Django.

## Zależności
Bolty wymagane: 001-local-runtime.
W tym bolcie poprzedzają: Brak.
Pełna identyfikacja story: 002-foundation-api/001-bootstrap-account.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
