---
id: 003-invitation-screens
unit: 003-household-foundation-ui
intent: 001-household-foundation
status: complete
priority: must
created: 2026-09-09T22:26:09.504Z
assigned_bolt: 006-household-foundation-ui
implemented: true
requirements: ["FR-04","FR-05"]
---
# Kopiowanie i przyjęcie zaproszeń

## User Story
Jako Owner lub zaproszona osoba chcę obsłużyć zaproszenie w przeglądarce, aby dołączyć konto bez e-maila.

## Kryteria akceptacji
- [x] Owner wybiera rolę, tworzy i kopiuje link oraz odwołuje zaproszenie; widzi termin ważności.
- [x] Link pozwala założyć konto albo zalogować się; po akceptacji użytkownik widzi właściwe gospodarstwo.
- [x] Wygasły, odwołany i zużyty link pokazuje czytelny komunikat; UI wyjaśnia, że link lokalny działa na komputerze z aplikacją.

## Zależności
Bolty wymagane: 005-foundation-api.
W tym bolcie poprzedzają: 001-account-screens, 002-household-screens.
Pełna identyfikacja story: 003-household-foundation-ui/003-invitation-screens.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.

