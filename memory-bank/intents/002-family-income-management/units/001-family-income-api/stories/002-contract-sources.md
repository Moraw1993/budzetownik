---
id: 002-contract-sources
unit: 001-family-income-api
intent: 002-family-income-management
status: complete
priority: must
created: '2026-09-23T08:26:40Z'
assigned_bolt: 010-family-income-api
implemented: true
requirements:
  - FR-03
  - FR-05
  - FR-07
---

# Umowa jako źródło dochodu członka

## User Story

Jako Administrator chcę dodać umowę członka z firmą i kwotą brutto, aby później móc wskazać ją jako źródło na karcie miesiąca.

## Kryteria akceptacji

- [ ] Umowa wybiera członka i aktywną firmę tego samego gospodarstwa, typ praca/zlecenie/dzieło/inne, datę początku i opcjonalny koniec, walutę, kwotę brutto oraz podstawę miesięcznie/godzinowo/za całość.
- [ ] Stanowisko jest dostępne przy pracy i zleceniu; typ „inne” ma czytelną nazwę szczegółową. Data końca nie poprzedza początku, a kwota jest nieujemną liczbą dziesiętną o precyzji dwóch miejsc.
- [ ] Jedna osoba może mieć wiele umów, również z tą samą firmą; każda ma własny identyfikator źródła i jest odróżnialna na liście.
- [ ] Zapis, zmiana i archiwizacja umowy są atomowe z audytem. Nie tworzą przychodu miesięcznego i nie kopiują brutto do domyślnej miesięcznej kwoty źródła.
- [ ] Backend odrzuca obcego członka lub firmę oraz zapis Member/Viewer.

## Zależności

001-company-dictionary; istniejący `IncomeSource` i reguły gospodarstwa.
