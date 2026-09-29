---
id: 003-other-source-and-conversion
unit: 002-family-management-ui
intent: 002-family-income-management
status: draft
priority: must
created: 2026-09-23T08:26:40Z
assigned_bolt: 011-family-management-ui
implemented: false
requirements: ["FR-04", "FR-05", "FR-06", "FR-07"]
---

# Inne źródło i jawna konwersja

## User Story

Jako Administrator chcę zarządzać innymi źródłami oraz świadomie uzupełnić stare „Wynagrodzenie” jako umowę, gdy to właściwe.

## Kryteria akceptacji

- [ ] „Dodaj inne źródło dochodu” pozwala wybrać osobę albo całe gospodarstwo i zapisać źródło bez firmy oraz kwoty umowy. Domyślna miesięczna kwota jest opcjonalną podpowiedzią.
- [ ] Akcja „Przekształć w umowę” przy starym źródle zbiera firmę, typ, brutto, podstawę i brakujące dane; przed zapisem pokazuje, że nie doda przychodu za miesiąc.
- [ ] Istniejące źródło pozostaje innym źródłem, dopóki użytkownik jawnie nie wykona przekształcenia.
- [ ] Widok odróżnia kwotę podpowiedzi od brutto i pokazuje archiwalne rekordy bez możliwości edycji.

## Zależności

001-family-navigation, 002-contract-company-forms i API bolta 010.
