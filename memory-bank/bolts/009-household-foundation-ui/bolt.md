---
id: 009-household-foundation-ui
unit: 003-household-foundation-ui
intent: 001-household-foundation
type: simple-construction-bolt
status: complete
stories:
  - 006-responsive-content-density
created: '2026-09-23T07:22:20Z'
started: '2026-09-23T07:22:20Z'
completed: '2026-09-23T20:23:35Z'
current_stage: null
stages_completed:
  - name: plan
    completed: '2026-09-23T07:39:13Z'
    artifact: implementation-plan.md
  - name: implement
    completed: '2026-09-23T08:11:20Z'
    artifact: implementation-walkthrough.md
  - name: test
    completed: '2026-09-23T20:23:12Z'
    artifact: test-walkthrough.md
requires_bolts:
  - 007-household-foundation-ui
enables_bolts:
  - 008-local-acceptance
requires_units:
  - 001-local-runtime
  - 002-foundation-api
blocks: true
complexity:
  avg_complexity: 1
  avg_uncertainty: 1
  max_dependencies: 1
  testing_scope: 3
---

# Gęstość i responsywność ekranów gospodarstwa

## Cel

Usunąć nieuzasadnione puste obszary z ekranów gospodarstwa i nadać prostym oraz złożonym formularzom odpowiednią szerokość, zachowując czytelność, dostępność i działanie na małych ekranach.

## Stories

- [ ] [006-responsive-content-density](../../intents/001-household-foundation/units/003-household-foundation-ui/stories/006-responsive-content-density.md): Zwarty, responsywny układ selektora, członków, relacji i dochodów.

## Wyniki

Jawne warianty układu paneli i formularzy, responsywne siatki dla ekranów danych, testy trzech docelowych szerokości oraz porównawcze zrzuty po zmianie.

Plan zatwierdzony przez użytkownika poleceniem „kontynuuj pracę”. Po zamknięciu bolta 007 wykonano implementację i uwzględniono zaakceptowaną uwagę o położeniu „Dostępów”. [Raport implementacji](implementation-walkthrough.md) i [raport testów](test-walkthrough.md) zatwierdzone.

## Etapy

- [x] Plan
- [x] Implementacja
- [x] Testy

## Zależności

Bolt 007 musi zostać zakończony przed implementacją. Bolt 009 poprzedza końcowy odbiór 008, aby odbiór obejmował poprawiony układ.

## Warunki zakończenia

Kryteria story są potwierdzone na szerokim, pośrednim i mobilnym widoku. Istniejące operacje, uprawnienia, testy funkcjonalne oraz dostępność klawiaturowa nie mają regresji.
