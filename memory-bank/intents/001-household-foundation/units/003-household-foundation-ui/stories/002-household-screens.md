---
id: 002-household-screens
unit: 003-household-foundation-ui
intent: 001-household-foundation
status: complete
priority: must
created: 2026-09-09T22:26:09.504Z
assigned_bolt: 006-household-foundation-ui
implemented: true
requirements: ["FR-02","FR-03","FR-05"]
---
# Gospodarstwa i role w interfejsie

## User Story
Jako użytkownik chcę wybrać gospodarstwo i zobaczyć swój dostęp, aby pracować w prawidłowym kontekście.

## Kryteria akceptacji
- [x] Można utworzyć gospodarstwo, zobaczyć listę swoich gospodarstw i przełączyć aktywne.
- [x] Zmiana gospodarstwa usuwa poprzednie dane i trwające odpowiedzi nie nadpisują nowego kontekstu.
- [x] Owner ma ekran zarządzania rolami; Member/Viewer widzą tryb odczytu; odmowa API jest obsłużona bez pozornego sukcesu.

## Zależności
Bolty wymagane: 005-foundation-api.
W tym bolcie poprzedzają: 001-account-screens.
Pełna identyfikacja story: 003-household-foundation-ui/002-household-screens.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.

