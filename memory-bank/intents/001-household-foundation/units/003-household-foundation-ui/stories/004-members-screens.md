---
id: 004-members-screens
unit: 003-household-foundation-ui
intent: 001-household-foundation
status: complete
priority: must
created: 2026-09-09T22:26:09.504Z
assigned_bolt: 007-household-foundation-ui
implemented: true
requirements: ["FR-06","FR-07"]
---
# Członkowie i relacje w interfejsie

## User Story
Jako Administrator chcę edytować członków i relacje, aby utrzymać aktualny opis rodziny.

## Kryteria akceptacji
- [x] Lista i formularze pozwalają dodać członka bez konta, zmienić relację oraz powiązać istniejące konto według zasad API.
- [x] Member/Viewer nie widzą aktywnych kontrolek zapisu; uprawnienia są weryfikowane ponownie przez serwer.
- [x] Dezaktywacja wymaga świadomego działania i pokazuje wynik; pusta lista i błędy mają zrozumiałe stany.

## Zależności
Bolty wymagane: 006-household-foundation-ui.
W tym bolcie poprzedzają: Brak.
Pełna identyfikacja story: 003-household-foundation-ui/004-members-screens.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
