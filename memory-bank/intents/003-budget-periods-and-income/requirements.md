---
intent: 003-budget-periods-and-income
phase: inception
status: in-progress
created: '2026-10-06T20:09:33Z'
updated: '2026-10-06T20:31:50Z'
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
- **Acceptance Criteria**: Utworzenie roku nie aktywuje żadnego miesiąca; miesiąc nieaktywny nie przyjmuje wpisów przychodu; użytkownik z uprawnieniem do edycji może jawnie aktywować wybrany miesiąc; wiele miesięcy może być aktywnych jednocześnie; można aktywować miesiące w dowolnej kolejności; status miesiąca jest widoczny.
- **Priority**: Must

### FR-03: Wpisy rzeczywistego przychodu
- **Description**: W aktywnym miesiącu użytkownik może zapisać wiele odrębnych wpisów rzeczywiście uzyskanego przychodu. Wpis wskazuje osobę będącą odbiorcą albo całe gospodarstwo.
- **Acceptance Criteria**: Jeden miesiąc może zawierać wiele przychodów tej samej osoby, gospodarstwa oraz źródła; kwota wpisu opisuje rzeczywiście uzyskany przychód i nie jest automatycznie kopiowana z kwoty brutto umowy ani podpowiedzi źródła; odbiorca wpisu należy do aktywnego gospodarstwa.
- **Priority**: Must

### FR-04: Słownik źródeł przychodu
- **Description**: Każdy wpis wskazuje pozycję ze słownika `IncomeSource`; dowolny tekst wpisany bezpośrednio jako źródło przychodu jest niedozwolony. W oknie dodawania przychodu użytkownik może w prosty sposób dodać nowe źródło do słownika i następnie użyć go we wpisie.
- **Acceptance Criteria**: Po wyborze członka dostępne są jego umowy aktywne w wybranym okresie oraz przypisane do niego pozostałe źródła; wpis gospodarstwa może wskazać źródło należące do gospodarstwa; nowe źródło jest tworzone z użyciem walidacji i pól właściwych dla jego typu, nie jako luźny tekst; źródła innych osób/gospodarstw nie mogą być wybrane; rozróżnialne są umowy/praca i pozostałe źródła, takie jak lokaty, odsetki, świadczenia lub 800+; powiązanie źródła jest dostępne przy późniejszym odczycie wpisu.
- **Priority**: Must

### FR-05: Kwota, waluta i data uzyskania
- **Description**: Każdy wpis zawiera rzeczywistą kwotę, walutę i datę uzyskania przychodu.
- **Acceptance Criteria**: Kwota zachowuje precyzję dziesiętną; waluta jest zapisana dla wpisu; data jest zapisana jako data faktycznego uzyskania przychodu; data uzyskania nie musi należeć do miesiąca rozliczeniowego, np. wypłata otrzymana 30 września może zostać ujęta w rozliczeniu października; sumy okresu i roku są prezentowane osobno dla każdej waluty, bez niejawnego przeliczania.
- **Priority**: Must

### FR-06: Załączniki do przychodu
- **Description**: Użytkownik może dołączyć wiele dokumentów potwierdzających jeden wpis przychodu.
- **Acceptance Criteria**: Załączniki pozostają powiązane z właściwym wpisem i gospodarstwem; obsługiwane są pliki PNG, JPG/JPEG i PDF; dostęp do nich podlega uprawnieniom tego wpisu; nie są publicznie dostępne bez autoryzacji.
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
| „Osoba lub inny obiekt” oznacza członka rodziny albo całe gospodarstwo. | Wpisy mogą wymagać innych właścicieli, np. celu lub konta. | Granica potwierdzona przez użytkownika; rozszerzenia właścicieli pozostają poza zakresem. |
| Owner i Administrator mogą zapisywać; Member i Viewer mają tylko odczyt. | Zmiana ról może naruszyć uzgodnione zasady dostępu. | Zachować istniejącą politykę bez rozszerzania uprawnień. |
| Każdy wpis wskazuje istniejące lub dodane z formularza źródło ze słownika `IncomeSource`. | Użytkownik może nie znaleźć pasującej kategorii albo pól źródła. | Szybkie dodawanie tworzy pełny, walidowany element słownika; pole swobodnego tekstu jest zabronione. |
| Suma w różnych walutach nie jest przeliczana w tym zakresie. | Użytkownik może oczekiwać jednej sumy w walucie gospodarstwa. | Pokazywać sumy per waluta; przeliczenia zaplanować osobno. |

## Open Questions

| Question | Owner | Due Date | Resolution |
| --- | --- | --- | --- |
| Czy „każdy z opcją edycji” oznacza istniejący model: Owner/Administrator zapisują, Member/Viewer tylko odczytują? | User | Checkpoint 2 | Resolved: Owner/Administrator write; Member/Viewer read-only |
| Jakie limity liczby i rozmiaru załączników są potrzebne? | User | Construction design | Pending; wiele plików na wpis; PNG, JPG/JPEG i PDF |
| Które dane źródła i odbiorcy trzeba zachować przy przychodzie jako historyczny stan, jeśli słownik lub przypisanie zmieni się później? | User | Construction design | Pending |
