---
unit: 003-periods-income-ui
intent: 003-budget-periods-and-income
unit_type: frontend
default_bolt_type: simple-construction-bolt
phase: inception
status: draft
created: '2026-10-06T20:32:37Z'
updated: '2026-10-06T20:32:37Z'
---

# Interfejs okresów i przychodów

## Cel i granica

Udostępnić w obecnej aplikacji webowej nawigację po latach i miesiącach, jawne akcje stanu, listę rzeczywistych przychodów, formularz wyboru źródła/szybkiego dodania oraz sumy per waluta. Jednostka konsumuje API; backend pozostaje źródłem prawdy dla reguł i autoryzacji.

## Wymagania obsługiwane

UI uczestniczy w widocznej realizacji FR-01–FR-08. Właścicielami reguł pozostają wyłącznie jednostki API zdefiniowane w `units.md`.

## Interakcje

- Pokazuje rok z 12 miesiącami i czytelny stan `inactive`, `active` lub `closed`.
- Pokazuje osobne, potwierdzane akcje aktywacji, zamknięcia i ponownego otwarcia stosownie do stanu i uprawnień.
- Formularz wymaga odbiorcy i pozycji słownikowej; przy osobie prezentuje umowy aktywne w okresie i inne przypisane źródła. Szybkie dodanie źródła prowadzi przez właściwy formularz słownika, bez pola wolnego tekstu.
- Pozwala wpisać rzeczywistą kwotę, walutę, datę uzyskania niezależną od miesiąca rozliczeniowego i wiele plików obsługiwanych formatów.
- Pokazuje sumy okresu grupowane według waluty, stan zamknięcia i ograniczenia edycji.

## Zależności i bramka projektowa

Zależy od 001-periods-api i 002-monthly-income-api oraz istniejącego 002-family-management-ui. Bolt 016 może rozpocząć implementację dopiero po planie wizualnym, wizualizacji, niezależnej ocenie wyniku **powyżej 7,5/10** i jawnej akceptacji zgodnie z `memory-bank/standards/ui-design-review.md`. Wymaganie dotyczy planowania: tej akceptacji nie zastępuje niniejszy intent.

## Stories

Do utworzenia: 001-navigate-periods, 002-change-period-state, 003-add-income-recipient-source, 004-enter-income-details, 005-manage-attachments-and-totals.

## Wyłączenia

Brak logiki obliczeniowej domeny, omijania uprawnień API, ręcznego wpisu nazwy źródła ani budżetowania wydatków.
