---
unit: 001-periods-api
bolt: 013-periods-api
stage: model
status: complete
created: '2026-10-07T09:57:59Z'
updated: '2026-10-07T09:57:59Z'
---

# Static Model — 001-periods-api

## Bounded Context

**Okresy rozliczeniowe** reprezentują kalendarzowe lata i miesiące gospodarstwa oraz ich cykl życia. Kontekst zarządza strukturą okresów i dostępnością miesiąca do zapisów. Nie przechowuje budżetu, planowanych kwot ani rzeczywistych przychodów; przyszły kontekst przychodów odwołuje się do miesiąca i respektuje jego stan.

## Domain Entities

| Entity | Properties | Business Rules |
| --- | --- | --- |
| `AccountingYear` | Tożsamość roku; `household_id`; rok kalendarzowy; data utworzenia; kolekcja miesięcy. | Dla jednego gospodarstwa i roku istnieje najwyżej jeden rok. Utworzenie tworzy pełny zestaw 12 kolejnych miesięcy od stycznia do grudnia; częściowy rok nie jest widoczny jako wynik udanej operacji. |
| `AccountingMonth` | Tożsamość miesiąca; numer 1–12; stan; moment aktywacji; moment zamknięcia. Jest częścią `AccountingYear`. | Każdy numer miesiąca występuje dokładnie raz w swoim roku. Przy utworzeniu każdy miesiąc ma stan `inactive`. Tylko `active` dopuszcza zapisy. `closed` blokuje dodawanie, edycję i usuwanie do jawnego ponownego otwarcia. |

`AccountingYear` i `AccountingMonth` należą do dokładnie jednego gospodarstwa. Członkostwo i role są istniejącymi pojęciami gospodarstwa, nie kopiowanymi encjami w tym kontekście.

## Value Objects

| Value Object | Properties | Constraints |
| --- | --- | --- |
| `CalendarYear` | Rok kalendarzowy. | Wskazuje rok kalendarzowy, nie rok budżetowy ani dowolny opisany przedział. Zakres obsługiwanych wartości należy potwierdzić w projekcie technicznym. |
| `MonthNumber` | Numer miesiąca. | Liczba całkowita od 1 do 12. |
| `AccountingPeriodKey` | `household_id`, rok, numer miesiąca. | Jednoznacznie identyfikuje miesiąc rozliczeniowy w gospodarstwie; nie utożsamia daty otrzymania przychodu z okresem księgowania. |
| `MonthState` | `inactive`, `active`, `closed`. | Dozwolone przejścia: `inactive → active`, `active → closed`, `closed → active`. Nie ma automatycznego przejścia ani powrotu do `inactive`. |
| `CalendarMonthRange` | Początek i koniec miesiąca wyprowadzone z roku i numeru miesiąca. | Obejmuje cały miesiąc kalendarzowy; granice są używane do porównań okresu, np. w przyszłym wyborze aktywnej umowy. |

## Aggregates

| Aggregate Root | Members | Invariants |
| --- | --- | --- |
| `AccountingYear` | Dwanaście `AccountingMonth` o numerach 1–12. | Rok należy do jednego gospodarstwa i jest unikalny w tym gospodarstwie. Zestaw miesięcy jest kompletny, bez luk i duplikatów. Początkowo wszystkie są `inactive`. Zmiana stanu jednego miesiąca nie zmienia stanu pozostałych. Zapis stanu oraz odpowiadające zdarzenie audytowe mają zostać spójne. |

**Granica spójności:** rok jest agregatem, ponieważ kompletność dwunastu miesięcy jest niezmiennikiem strukturalnym. Operacje stanu wskazują pojedynczy miesiąc wewnątrz agregatu; mogą być wykonywane w dowolnej kolejności, a wiele miesięcy może pozostawać aktywnych jednocześnie. Sposób koordynacji współbieżnych zapisów i zamknięcia z przyszłymi wpisami przychodu należy opisać w Stage 2.

## Domain Events

| Event | Trigger | Payload |
| --- | --- | --- |
| `AccountingYearCreated` | Pomyślne utworzenie nowego roku. | Id gospodarstwa, rok, identyfikatory 12 utworzonych miesięcy, wykonawca i czas. |
| `AccountingMonthActivated` | Jawna aktywacja miesiąca `inactive`. | Id gospodarstwa, klucz okresu, poprzedni i nowy stan, wykonawca i czas. |
| `AccountingMonthClosed` | Jawne zamknięcie miesiąca `active`. | Id gospodarstwa, klucz okresu, poprzedni i nowy stan, wykonawca i czas. |
| `AccountingMonthReopened` | Jawne ponowne otwarcie miesiąca `closed`. | Id gospodarstwa, klucz okresu, poprzedni i nowy stan, wykonawca i czas. |

Zdarzenia opisują wyłącznie udane przejścia. Ponowienie żądania w stanie docelowym nie tworzy fikcyjnego przejścia ani drugiej zmiany stanu.

## Domain Services

| Service | Operations | Dependencies |
| --- | --- | --- |
| `AccountingYearCreationService` | Utworzenie nowego roku i pełnego zestawu miesięcy; odrzucenie duplikatu. | `AccountingYearRepository`; transakcyjny kanał istniejącego audytu. |
| `AccountingPeriodLifecycle` | Aktywacja, zamknięcie i ponowne otwarcie miesiąca; kontrola dozwolonego przejścia. | Agregat `AccountingYear`; kanał istniejącego audytu. |

Autoryzacja aktora pozostaje obowiązkiem warstwy aplikacyjnej/API: Owner i Administrator mogą zapisywać, Member i Viewer odczytują. Usługa domenowa nie ufa identyfikatorom gospodarstwa ani roli podanym bez weryfikacji przez aplikację.

## Repository Interfaces

| Repository | Entity | Methods |
| --- | --- | --- |
| `AccountingYearRepository` | Agregat `AccountingYear` wraz z miesiącami. | `get_by_id(household_id, year_id)`, `get_by_calendar_year(household_id, year)`, `add(year)`, `save(year)`. Dostęp do agregatu musi być ograniczony gospodarstwem; semantyka transakcji/współbieżności powstanie w Stage 2. |
| `FinancialAuditPort` | Zdarzenie zmiany stanu okresu. | Zapis wykonawcy, czasu, obiektu oraz zmiany stanu w tej samej granicy transakcyjnej co zapis okresu. Wykorzystuje istniejący audyt; nie wprowadza nowego dziennika. |

## Coverage of Stories

- **001-create-year-months** — kompletność, unikalność i początkowy stan dwunastu miesięcy są niezmiennikami `AccountingYear`.
- **002-activate-month** — jawna niezależna zmiana stanu oraz `AccountingMonthActivated`.
- **003-close-and-reopen-month** — przejścia `active → closed → active`, blokada zapisów w stanie `closed` i audytowane zdarzenia.

## Ubiquitous Language

| Term | Definition |
| --- | --- |
| Rok rozliczeniowy | Rok kalendarzowy gospodarstwa, który zawsze obejmuje 12 miesięcy od stycznia do grudnia. |
| Miesiąc rozliczeniowy | Jeden konkretny miesiąc kalendarzowy przypisany do roku i gospodarstwa; to jego przypisanie, a nie data otrzymania środków, określa okres ewidencji. |
| Nieaktywny (`inactive`) | Miesiąc utworzony, lecz nieuruchomiony; nie przyjmuje wpisów przychodu. |
| Aktywny (`active`) | Jawnie uruchomiony miesiąc, w którym dozwolone są wpisy przychodu dla uprawnionych ról. |
| Zamknięty (`closed`) | Zakończony miesiąc, którego wpisów nie można zmieniać przed jawnym ponownym otwarciem. |
| Aktywacja | Jawne przejście miesiąca `inactive → active`; nie aktywuje żadnego innego miesiąca. |
| Ponowne otwarcie | Jawne przejście `closed → active`, które przywraca możliwość zmian. |
| Okres kalendarzowy | Data początku i końca wynikająca z roku i numeru miesiąca; może służyć do porównania zakresu dat innych domen. |

## Decisions Deferred to Technical Design

- Szczegółowy zakres dopuszczalnych lat i walidacja dat.
- Dokładne mechanizmy unikalności i ochrony przed równoległym tworzeniem/zmianą stanu.
- Koordynacja zamknięcia miesiąca z zapisem przychodu, tak aby nie zaakceptować zapisu po zamknięciu.
- Kształt komunikatów i integracja zmian stanu z istniejącym audytem, bez powielania jego modelu.
