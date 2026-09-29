---
id: 001-account-screens
unit: 003-household-foundation-ui
intent: 001-household-foundation
status: complete
priority: must
created: 2026-09-09T22:26:09.504Z
assigned_bolt: 006-household-foundation-ui
implemented: true
requirements: ["FR-01"]
---
# Konfiguracja i logowanie w przeglądarce

## User Story
Jako użytkownik chcę skonfigurować konto i zalogować się, aby rozpocząć pracę bez ręcznych wywołań API.

## Kryteria akceptacji
- [x] Pusta instalacja prowadzi do utworzenia pierwszego konta; istniejąca do logowania; błędy formularza nie gubią niesekretnych pól.
- [x] Wylogowanie usuwa chronione dane z widoku; cofnięcie strony nie pokazuje dostępnego panelu poprzedniego użytkownika.
- [x] Formularze mają etykiety i obsługę klawiatury; UI nie prezentuje szczegółów błędów serwera.

## Zależności
Bolty wymagane: 005-foundation-api.
W tym bolcie poprzedzają: Brak.
Pełna identyfikacja story: 003-household-foundation-ui/001-account-screens.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.

