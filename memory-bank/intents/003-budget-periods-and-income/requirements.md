---
intent: 003-budget-periods-and-income
phase: inception
status: draft
created: '2026-10-06T20:09:33Z'
updated: '2026-10-06T20:09:33Z'
---

# Requirements: Okresy rozliczeniowe i rzeczywiste przychody

## Intent Overview

Umożliwić gospodarstwu tworzenie lat rozliczeniowych z dwunastoma miesiącami, jawne uruchamianie miesięcy oraz ewidencjonowanie rzeczywiście uzyskanych przychodów przypisanych do członka rodziny albo całego gospodarstwa. Przychody mogą pochodzić z wielu źródeł i zawierać kwotę, walutę, datę uzyskania oraz załącznik.

## Business Goals

| Goal | Success Metric | Priority |
| --- | --- | --- |
| Zapewnić stałą strukturę okresów rozliczeniowych | Każdy utworzony rok ma dokładnie 12 miesięcy; wszystkie zaczynają jako nieaktywne | Must |
| Umożliwić ewidencję faktycznych przychodów rodziny | Użytkownik zapisuje wiele odrębnych przychodów z przypisanym odbiorcą, źródłem lub sposobem uzyskania, kwotą, walutą i datą | Must |
| Chronić zamknięte okresy przed przypadkową zmianą | Edycja danych miesiąca jest możliwa dopiero po jego ponownym otwarciu | Must |

## Functional Requirements

### FR-01: Lata rozliczeniowe
- **Description**: Uprawniony użytkownik może utworzyć lub wybrać rok rozliczeniowy gospodarstwa.
- **Acceptance Criteria**: Rok zawiera dokładnie 12 miesięcy kalendarzowych od stycznia do grudnia; miesiące są powiązane z jednym gospodarstwem i nie dublują istniejącego roku; użytkownik może przejść z roku do jego miesięcy.
- **Priority**: Must

### FR-02: Jawne uruchamianie miesięcy
- **Description**: Każdy miesiąc zaczyna jako nieaktywny i wymaga jawnej aktywacji przez użytkownika rozpoczynającego jego prowadzenie.
- **Acceptance Criteria**: Utworzenie roku nie aktywuje żadnego miesiąca; miesiąc nieaktywny nie przyjmuje wpisów przychodu; użytkownik z uprawnieniem do edycji może jawnie aktywować wybrany miesiąc; status miesiąca jest widoczny.
- **Priority**: Must

### FR-03: Wpisy rzeczywistego przychodu
- **Description**: W aktywnym miesiącu użytkownik może zapisać wiele odrębnych wpisów rzeczywiście uzyskanego przychodu. Wpis wskazuje osobę będącą odbiorcą albo całe gospodarstwo.
- **Acceptance Criteria**: Jeden miesiąc może zawierać wiele przychodów tej samej osoby, gospodarstwa oraz źródła; kwota wpisu opisuje rzeczywiście uzyskany przychód i nie jest automatycznie kopiowana z kwoty brutto umowy ani podpowiedzi źródła; odbiorca wpisu należy do aktywnego gospodarstwa.
- **Priority**: Must

### FR-04: Źródło lub sposób uzyskania przychodu
- **Description**: Przy wyborze osoby system udostępnia jej umowy i źródła aktywne w wybranym okresie. Dla przychodu niezwiązanego z umową użytkownik może określić sposób jego uzyskania. Wpis gospodarstwa może wskazać źródło należące do gospodarstwa.
- **Acceptance Criteria**: Lista umów uwzględnia daty obowiązywania w danym okresie; źródło przypisane do innej osoby lub gospodarstwa nie może zostać wybrane; można odróżnić przychód związany z umową/pracą od pozostałych, takich jak lokaty, odsetki, świadczenia lub 800+; informacja o źródle pozostaje dostępna przy późniejszym odczycie wpisu.
- **Priority**: Must

### FR-05: Kwota, waluta i data uzyskania
- **Description**: Każdy wpis zawiera rzeczywistą kwotę, walutę i datę uzyskania przychodu.
- **Acceptance Criteria**: Kwota zachowuje precyzję dziesiętną; waluta jest zapisana dla wpisu; data jest zapisana jako data uzyskania przychodu; sumy okresu i roku są prezentowane osobno dla każdej waluty, bez niejawnego przeliczania.
- **Priority**: Must

### FR-06: Załączniki do przychodu
- **Description**: Użytkownik może dołączyć dokument potwierdzający wpis przychodu.
- **Acceptance Criteria**: Załącznik pozostaje powiązany z właściwym wpisem i gospodarstwem; dostęp do niego podlega uprawnieniom tego wpisu; nie jest publicznie dostępny bez autoryzacji.
- **Priority**: Should

### FR-07: Zamknięcie i ponowne otwarcie miesiąca
- **Description**: Uprawniony użytkownik może zamknąć miesiąc; przed edycją zamkniętego miesiąca musi jawnie go ponownie otworzyć.
- **Acceptance Criteria**: Zamknięcie blokuje dodawanie, edycję i usuwanie wpisów miesiąca; ponowne otwarcie przywraca te operacje; status miesiąca jest widoczny; zmiana statusu i istotne zmiany wpisów podlegają audytowi zgodnie ze standardami projektu.
- **Priority**: Must

### FR-08: Podsumowania okresów
- **Description**: Użytkownik widzi przychody miesiąca i roku w kontekście wybranego gospodarstwa.
- **Acceptance Criteria**: Podsumowanie miesiąca i roku opiera się na zapisanych wpisach rzeczywistych; kwoty są grupowane według waluty; podsumowanie nie obejmuje kwot konfiguracyjnych z umów ani podpowiedzi źródeł.
- **Priority**: Must

## Non-Functional Requirements

### Security and data integrity
- Odczyt, zapis, aktywacja, zamknięcie i ponowne otwarcie podlegają istniejącym uprawnieniom gospodarstwa i izolacji tenantów.
- Załączniki finansowe są dostępne wyłącznie dla uprawnionych członków gospodarstwa i są chronione przed publicznym dostępem.
- Zapis wpisu, jego powiązań i wpisu audytowego jest atomowy.
- Wymagane role edycji pozostają zgodne z ustalonym modelem Owner/Administrator/Member/Viewer, o ile przegląd wymagań nie zatwierdzi zmiany.

### Reliability
- Utworzenie roku gwarantuje komplet 12 miesięcy bez duplikatów, także przy równoległych żądaniach.
- Zamknięcie miesiąca skutecznie blokuje równoległe zapisy po jego zamknięciu.
- Dane okresów, przychodów i załączników zachowują trwałość po restarcie aplikacji.

## Constraints

### Technical Constraints
- **Project-wide standards**: Wykorzystać standardy z `memory-bank/standards/`; Construction ponownie sprawdzi istniejące modele i API przed projektowaniem.
- **Intent-specific constraints**: Wykorzystać istniejące gospodarstwa, członków, role oraz model `IncomeSource`/`Contract` jako wejście do projektu. Nie mieszać konfiguracji źródeł z rzeczywistymi przychodami.

### Business Constraints
- Zakres obejmuje wyłącznie lata/miesiące rozliczeniowe i rzeczywiste przychody.
- Wydatki, planowanie budżetu, automatyczne wyliczanie netto, integracje bankowe i automatyczne tworzenie przychodów z umów pozostają poza zakresem.

## Assumptions

| Assumption | Risk if Invalid | Mitigation |
| --- | --- | --- |
| „Osoba lub inny obiekt” oznacza członka rodziny albo całe gospodarstwo. | Wpisy mogą wymagać innych właścicieli, np. celu lub konta. | Potwierdzić granicę na przeglądzie wymagań przed dalszym planowaniem. |
| Edycja jest dostępna dla ról z prawem edycji danych gospodarstwa według istniejącej polityki. | Zmiana ról może naruszyć uzgodnione zasady dostępu. | Nie rozszerzać uprawnień Member/Viewer bez jawnej decyzji. |
| Aktywne źródła „other” mogą reprezentować przychody niebędące umowami, a wpis zachowuje historyczny opis źródła. | Samo wskazanie źródła może nie wystarczyć do opisania nietypowego wpływu. | Doprecyzować czy potrzebne jest dodatkowe pole metody lub swobodny opis. |
| Suma w różnych walutach nie jest przeliczana w tym zakresie. | Użytkownik może oczekiwać jednej sumy w walucie gospodarstwa. | Pokazywać sumy per waluta; przeliczenia zaplanować osobno. |

## Open Questions

| Question | Owner | Due Date | Resolution |
| --- | --- | --- | --- |
| Czy każdy użytkownik gospodarstwa z rolą Member może edytować/aktywować/zamykać miesiąc, czy obowiązuje istniejący podział ról? | User | Checkpoint 2 | Pending |
| Czy źródło przychodu wybieramy z istniejących `IncomeSource` (umowa/other), czy wpis ma pozwalać na jednorazową nazwę/metodę bez uprzedniego konfigurowania źródła? | User | Checkpoint 2 | Pending |
| Czy data uzyskania musi przypadać w obrębie wybranego miesiąca rozliczeniowego? | User | Checkpoint 2 | Pending |
| Czy wiele miesięcy może być aktywnych równocześnie i czy można aktywować miesiące w dowolnej kolejności? | User | Checkpoint 2 | Pending |
| Czy jeden wpis może mieć wiele załączników i jakie typy/limity plików są potrzebne? | User | Construction design | Pending |
