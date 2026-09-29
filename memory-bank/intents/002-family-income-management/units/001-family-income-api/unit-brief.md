---
unit: 001-family-income-api
intent: 002-family-income-management
unit_type: backend
default_bolt_type: ddd-construction-bolt
phase: construction
status: complete
created: '2026-09-23T08:24:02Z'
updated: '2026-09-23T21:12:14Z'
---

# API firm, umów i źródeł dochodu

## Cel i granica

Rozszerzyć istniejący modularny monolit Django. Jednostka odpowiada za trwałość danych, izolację gospodarstw, walidację, migrację i audyt. Nie zapisuje przychodów za miesiąc.

## Wymagania przypisane

FR-02, FR-03, FR-04, FR-05, FR-06 i FR-07. FR-01 należy do UI; backend dostarcza mu istniejących członków i nowe zasoby. Cel jakościowy: po migracji żaden istniejący identyfikator źródła ani wpis audytu nie znika.

## Proponowane encje

| Encja | Znaczenie i pola |
| --- | --- |
| `Company` | Słownik gospodarstwa: identyfikator, `household`, wymagana nazwa, status archiwalny i metadane zmiany. Firma użyta przez umowę nie jest fizycznie usuwana. |
| `IncomeSource` | Wspólny wybieralny obiekt: obecne pola właściciela, nazwy, dat, waluty i statusu oraz `kind` = `contract` lub `other`. Istniejące rekordy otrzymują `other`. `default_monthly_amount`, kategoria, płatnik i częstotliwość dotyczą innych źródeł; kwota jest opcjonalną podpowiedzią. Szczegóły umowy nie wykorzystują tych pól do przechowywania brutto. |
| `Contract` | Szczegóły umowy powiązane 1:1 z `IncomeSource`: firma, typ (`employment`, `mandate`, `specific_work`, `other`), opcjonalne stanowisko, kwota brutto jako Decimal, podstawa (`monthly`, `hourly`, `total`) i ewentualna własna nazwa typu „inne”. Właściciel i daty pochodzą ze źródła, aby nie dublować stanu. |
| `AuditLog` | Istniejący dziennik; rozszerzony o zdarzenia firm i umów oraz jawnej konwersji źródła. Zapisy powstają w tej samej transakcji co zmiana. |

## Reguły domenowe

- Umowa wymaga aktywnego członka i firmy z tego samego gospodarstwa; inne źródło może mieć `member_id = null`.
- `kind = contract` wymaga szczegółów `Contract`, a `kind = other` ich nie ma. API nie ujawnia stanu częściowo zapisanego.
- Data końca nie może poprzedzać początku. Zmiana powiązań między gospodarstwami jest odrzucana.
- `gross_amount` i jego podstawa nie są kopiowane do `default_monthly_amount`; nie ma wyliczania netto ani przychodu miesięcznego.
- Formularz i API umowy nadają źródłu rozpoznawalną nazwę na przyszłej liście wyboru. Pola inne niż wspólne, odziedziczone ze starego źródła, pozostają puste lub nie są przyjmowane dla `contract`.
- Przekształcenie istniejącego źródła w umowę jest jawne i wymaga brakujących danych. Zachowuje identyfikator źródła oraz poprzedni stan w audycie; nie przekształca rekordów podczas samej migracji.
- Archiwizacja firmy powiązanej z umową i archiwizacja członka nie zrywają historii. Nowe powiązania można tworzyć tylko do aktywnych obiektów.

## Interfejs API do zaprojektowania w bolcie

- Zasób `companies/` do listowania, tworzenia, edycji i archiwizacji firm.
- Zasób `contracts/` do listowania, tworzenia, edycji i archiwizacji umów. Identyfikator źródła pozostaje stabilny i dostępny do przyszłego wyboru na karcie miesiąca.
- Istniejący `income-sources/` obsługuje inne źródła i zachowuje czytelny odczyt istniejących rekordów. Kontrakt odpowiedzi pozwala rozróżnić `kind` i właściciela bez zgadywania z nazwy „Wynagrodzenie”.
- Jawna operacja przekształcenia starego źródła w umowę; szczegółowa ścieżka, walidacja współbieżności i kształt odpowiedzi powstaną w projekcie technicznym bolta.

## Migracja i zgodność

Nowa migracja dodaje firmę i szczegóły umowy, oznacza dotychczasowe źródła jako `other` i dopuszcza brak domyślnej kwoty. Zachowuje dotychczasowe kwoty, UUID, daty, powiązania, status i `AuditLog`. Test migracyjny zaczyna od schematu przed zmianą i sprawdza zapis oraz odczyt po zmianie. Nie usuwa starego API bez planu zgodności.

## Stories

- [001-company-dictionary](stories/001-company-dictionary.md)
- [002-contract-sources](stories/002-contract-sources.md)
- [003-other-sources](stories/003-other-sources.md)
- [004-legacy-source-migration](stories/004-legacy-source-migration.md)

Łącznie 4 stories Must; wszystkie zaplanowane w bolcie 010.

## Bolt i zależności

Bolt [010-family-income-api](../../../../bolts/010-family-income-api/bolt.md) po zakończeniu 008-local-acceptance. Interfejs 002-family-management-ui zależy od kontraktów API tej jednostki.

## Kryteria zakończenia

- Operacje firm, umów, źródeł i konwersji przechodzą testy ról, izolacji, walidacji dziesiętnej, dat oraz audytu.
- Migracja zachowuje istniejące dane i nie generuje umów ani miesięcznych przychodów.
- API dostarcza stabilną listę źródeł do przyszłego wyboru na karcie miesiąca.
