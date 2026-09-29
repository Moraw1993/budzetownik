---
unit: 003-family-income-acceptance
intent: 002-family-income-management
unit_type: infrastructure
default_bolt_type: simple-construction-bolt
phase: construction
status: in-progress
created: 2026-09-23T08:24:02Z
updated: 2026-09-29T21:07:18Z
---

# Odbiór modelu rodziny i źródeł

## Cel i granica

Sprawdzić po połączeniu API i interfejsu zachowanie na lokalnej instalacji oraz migrację przykładowych danych ze starego schematu. Nie dodaje nowych reguł domenowych ani miesięcznych przychodów.

## Wymagania przypisane

Weryfikacja FR-01–FR-07, ze szczególnym naciskiem na FR-06 i FR-07. Jednostka nie przejmuje własności tych wymagań od API i UI.

## Scenariusze odbioru

- Po migracji stare „Wynagrodzenie” zachowuje identyfikator, kwotę podpowiedzi, członka i audyt; jest innym źródłem, dopóki użytkownik jawnie nie uzupełni umowy.
- Owner dodaje firmę, dwie umowy jednej osoby i jedno inne źródło gospodarstwa; kwota brutto nie tworzy przychodu miesięcznego.
- Member i Viewer odczytują dane i nie mogą ich zmieniać nawet przez bezpośrednie żądania API.
- Obce gospodarstwo i jego firma, członek lub źródło nie mogą zostać powiązane ani odczytane.
- Ponowne uruchomienie lokalnych kontenerów bez usuwania wolumenów zachowuje firmy, umowy i źródła.

## Stories

- [001-migration-and-isolation](stories/001-migration-and-isolation.md)
- [002-family-user-journey](stories/002-family-user-journey.md)

Łącznie 2 stories Must; obie zaplanowane w bolcie 012.

## Bolt i zależności

Bolt [012-family-income-acceptance](../../../../bolts/012-family-income-acceptance/bolt.md) po bolcie 011-family-management-ui. Dane testowe są syntetyczne; test nie usuwa danych użytkownika.

## Kryteria zakończenia

- Scenariusze przechodzą na lokalnej instalacji, a wyniki i ograniczenia są zapisane w raporcie testowym bolta.
- Kontrola jakości projektu i odpowiednie testy API oraz UI przechodzą bez wyłączania reguł.
