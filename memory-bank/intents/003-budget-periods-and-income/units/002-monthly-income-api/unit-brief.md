---
unit: 002-monthly-income-api
intent: 003-budget-periods-and-income
unit_type: backend
default_bolt_type: ddd-construction-bolt
phase: inception
status: draft
created: '2026-10-06T20:32:37Z'
updated: '2026-10-07T11:21:40Z'
---

# API rzeczywistych przychodów

## Cel i granica

Dodać w modularnym monolicie Django trwałe wpisy rzeczywiście uzyskanych przychodów, przypisane do gospodarstwa, miesiąca oraz osoby lub gospodarstwa. Wpis jest odrębny od konfiguracji źródła i kwoty umowy.

## Wymagania przypisane

Właściciel reguł: FR-03, FR-04, FR-05, FR-06 i FR-08. Wpis wskazuje dokładnie jedno źródło `IncomeSource` ze słownika. Nie dopuszcza wolnego tekstu jako źródła.

## Zakres zachowania

- Create/edit/delete wpisów jest dozwolone wyłącznie w `active` miesiącu; API stosuje `locked_access` (`Household`), następnie blokuje `AccountingYear`, sprawdza stan i wykonuje zapis wraz z audytem w jednej krótkiej transakcji. Bolt 014 testuje wszystkie trzy mutacje przeciwko równoległemu close na PostgreSQL.
- Odbiorca to członek gospodarstwa albo całe gospodarstwo. Dla członka dostępne są jego umowy aktywne w okresie oraz pozostałe przypisane mu źródła; źródła gospodarstwa dostępne są dla wpisu gospodarstwa.
- Szybkie dodanie tworzy walidowany element `IncomeSource` zgodny z jego typem, po czym wybiera ten element w przychodzie.
- Kwota jest wartością dziesiętną, waluta należy do wpisu, a data oznacza faktyczne otrzymanie i może leżeć poza miesiącem rozliczeniowym.
- Sumy miesięczne i roczne grupują zapisane kwoty osobno według waluty; nie przeliczają ich i nie pobierają wartości z umów ani domyślnych kwot źródeł.
- Załączniki wielu plików obsługuje osobny bolt 015; pozostają prywatne i powiązane z wpisem/gospodarstwem.
- Zachowanie historycznego obrazu źródła i odbiorcy oraz limity załączników pozostają decyzjami projektu technicznego przed implementacją.

## Podział boltów

- 014-monthly-income-api: wpisy, właściciel/źródło, waluta/data i podsumowania.
- 015-income-attachments-api: wielokrotne załączniki PNG, JPG/JPEG, PDF z limitami i autoryzowanym przechowywaniem/pobieraniem.

Jednostka zależy od 001-periods-api oraz istniejącego 001-family-income-api (źródła/umowy). Kontrakt 013 określa stany okresu, do których zapis przychodu się odnosi.

## Stories

Łącznie 4 stories Must i 1 Should; story 005 należy do osobnego bolta 015.

- [ ] **001-record-income** — Must — 014-monthly-income-api
- [ ] **002-select-dictionary-source** — Must — 014-monthly-income-api
- [ ] **003-record-amount-currency-date** — Must — 014-monthly-income-api
- [ ] **004-period-totals-by-currency** — Must — 014-monthly-income-api
- [ ] **005-private-income-attachments** — Should — 015-income-attachments-api

## Kryteria zakończenia

Testy API obejmują walidację kwot i dat, aktywny/zamknięty okres, role, izolację gospodarstw, odbiorcę/źródło, szybką walidowaną rejestrację źródła, podsumowania per waluta oraz prywatny dostęp do plików. Transakcja wpisu i audytu jest atomowa.

## Wyłączenia

Brak automatycznego wyliczania netto, kopiowania kwoty umowy do przychodu, kursów walut, integracji bankowej/OCR i swobodnego tekstu źródła.
