---
id: 001-end-to-end-acceptance
unit: 004-local-acceptance
intent: 001-household-foundation
status: complete
priority: must
created: '2026-09-09T22:26:09.504Z'
assigned_bolt: 008-local-acceptance
implemented: true
requirements:
  - NFR-01
  - NFR-03
---
# Odbiór całego fundamentu

## User Story
Jako właściciel produktu chcę wykonać scenariusz odbioru, aby potwierdzić działanie MVP 1.

## Kryteria akceptacji
- [ ] Na syntetycznych danych wykonano wszystkie sześć kroków scenariusza odbioru requirements.md.
- [ ] Testy obejmują Owner, Administrator, Member i Viewer, dwa gospodarstwa, żądania bez sesji, odwołanie dostępu i próby bezpośredniego dostępu do obcych obiektów.
- [ ] Raport pokazuje wynik każdego kryterium i rzeczywiste ograniczenia; testy nie korzystają z prywatnych arkuszy jako automatycznych danych startowych.

## Zależności
Bolty wymagane: 009-household-foundation-ui.
W tym bolcie poprzedzają: Brak.
Pełna identyfikacja story: 004-local-acceptance/001-end-to-end-acceptance.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
