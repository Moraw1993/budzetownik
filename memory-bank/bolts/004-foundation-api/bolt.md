---
id: 004-foundation-api
unit: 002-foundation-api
intent: 001-household-foundation
type: ddd-construction-bolt
status: complete
stories:
  - 007-issue-invitation
  - 008-accept-invitation
created: '2026-09-09T22:26:09.504Z'
started: '2026-09-11T19:12:05+02:00'
completed: '2026-09-11T17:42:42Z'
current_stage: null
stages_completed:
  - name: model
    completed: '2026-09-11T19:16:30+02:00'
    artifact: ddd-01-domain-model.md
  - name: design
    completed: '2026-09-11T19:19:07+02:00'
    artifact: ddd-02-technical-design.md
  - name: adr
    completed: '2026-09-11T19:23:28+02:00'
    artifact: adr-003-invitation-token-protection.md
  - name: implement
    completed: '2026-09-11T19:32:59+02:00'
    artifact: source-code
  - name: test
    completed: '2026-09-11T19:39:50+02:00'
    artifact: ddd-03-test-report.md
requires_bolts:
  - 003-foundation-api
enables_bolts:
  - 005-foundation-api
requires_units:
  - 001-local-runtime
blocks: true
complexity:
  avg_complexity: 2
  avg_uncertainty: 1
  max_dependencies: 2
  testing_scope: 2
---
# Zaproszenia bez e-maili

## Cel
Zaproszenia bez e-maili; zakres ograniczony do poniższych stories.

## Stories
- [ ] [007-issue-invitation](../../intents/001-household-foundation/units/002-foundation-api/stories/007-issue-invitation.md): Wydanie i odwołanie zaproszenia.
- [ ] [008-accept-invitation](../../intents/001-household-foundation/units/002-foundation-api/stories/008-accept-invitation.md): Przyjęcie zaproszenia.

## Wyniki
Kod i konfiguracja odpowiadające kryteriom stories, odpowiednie migracje, dokumentacja działania i raport rzeczywistych testów.




## Etapy
- [ ] Model domeny
- [ ] Projekt techniczny
- [ ] Analiza decyzji architektonicznych
- [ ] Implementacja
- [ ] Testy

## Zależności
Bolty: 003-foundation-api.
Jednostki wymagane: 001-local-runtime.
Status planned nie oznacza rozpoczętej pracy; blocks odzwierciedla niezakończone zależności.

## Warunki zakończenia
Wszystkie stories i kryteria zaakceptowane w testach, bez otwartych błędów naruszających wymagania. Dokumentacja raportuje ograniczenia środowiska.
