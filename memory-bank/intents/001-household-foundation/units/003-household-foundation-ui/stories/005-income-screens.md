---
id: 005-income-screens
unit: 003-household-foundation-ui
intent: 001-household-foundation
status: complete
priority: must
created: 2026-09-09T22:26:09.504Z
assigned_bolt: 007-household-foundation-ui
implemented: true
requirements: ["FR-08"]
---
# Źródła dochodu w interfejsie

## User Story
Jako Administrator chcę zarządzać źródłami dochodu, aby przygotować miesięczne planowanie.

## Kryteria akceptacji
- [x] Formularz udostępnia komplet pól FR-08, wybór gospodarstwa lub członka, kwotę i walutę.
- [x] Owner/Administrator dodaje, edytuje i dezaktywuje źródła; Member/Viewer ma odczyt.
- [x] Kwoty prezentowane są z walutą bez utraty precyzji, a widok wyjaśnia, że kwota domyślna nie jest rzeczywistą transakcją.

## Zależności
Bolty wymagane: 006-household-foundation-ui.
W tym bolcie poprzedzają: 004-members-screens.
Pełna identyfikacja story: 003-household-foundation-ui/005-income-screens.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
