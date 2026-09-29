---
id: 004-legacy-source-migration
unit: 001-family-income-api
intent: 002-family-income-management
status: complete
priority: must
created: '2026-09-23T08:26:40Z'
assigned_bolt: 010-family-income-api
implemented: true
requirements:
  - FR-06
  - FR-07
---

# Zachowanie i jawne przekształcenie istniejących źródeł

## User Story

Jako Owner chcę zachować stare źródła i zdecydować, które z nich są umowami, bez utraty historii.

## Kryteria akceptacji

- [ ] Migracja oznacza wszystkie dotychczasowe źródła jako `other`; zachowuje UUID, gospodarstwo, członka, kwotę, walutę, daty, status i wpisy audytu.
- [ ] Żadna nazwa ani kategoria, w tym „Wynagrodzenie”, nie powoduje automatycznego utworzenia umowy lub przychodu miesięcznego.
- [ ] Jawne przekształcenie istniejącego źródła wymaga aktywnego członka, firmy i pełnych danych umowy; zachowuje identyfikator źródła i zapisuje stan przed/po w audycie.
- [ ] Błąd walidacji lub równoczesna zmiana wycofuje całą operację; API nie pozostawia źródła `contract` bez szczegółów umowy.
- [ ] Odczyt dawnych źródeł przez obecny ekran/API działa do chwili zastąpienia interfejsu, bez ujawnienia danych innych gospodarstw.

## Zależności

001-company-dictionary, 002-contract-sources i 003-other-sources. Test na schemacie przed migracją.
