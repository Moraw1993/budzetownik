---
intent: 001-household-foundation
phase: inception
status: complete
created: '2026-09-09T22:18:51.076Z'
updated: '2026-09-23T21:10:12Z'
---

# Wymagania: Fundament gospodarstwa domowego

## Cel i źródła
MVP 1 umożliwia zalogowanie się, utworzenie gospodarstwa, określenie jego członków i źródeł dochodu oraz kontrolę dostępu. Źródło: [product-requirements.md](../../standards/product-requirements.md), sekcje 4–6, 49–50, 57–64 i BR-01–BR-03. Decyzje użytkownika: Django oraz lokalny Docker.
Wymagania i przedstawione doprecyzowania zatwierdzone przez użytkownika. Zakończono przegląd wymagań (checkpoint 2); przegląd planu realizacji pozostaje osobnym krokiem.

## Cele biznesowe
| Cel | Kryterium sukcesu | Priorytet |
|---|---|---|
| Reprezentacja rodziny | Członek bez konta i członek z kontem mogą należeć do tego samego gospodarstwa | Must |
| Przygotowanie danych do budżetu | Źródła dochodu można przypisać członkowi lub gospodarstwu | Must |
| Rozdzielenie gospodarstw | Użytkownik bez członkostwa nie uzyskuje danych gospodarstwa przez API | Must |
| Lokalna obsługa | Po uruchomieniu przez Docker użytkownik wykonuje podstawowy scenariusz w przeglądarce | Must |

## Zakres
Logowanie i wylogowanie, utworzenie pierwszego konta, dołączanie użytkowników do gospodarstwa, wybór aktywnego gospodarstwa, role, członkowie, typy relacji rodzinnych, źródła dochodu, podstawowy audyt i lokalne uruchomienie.

Poza zakresem tego etapu: miesięczne przychody i budżety, kredyty, transakcje oszczędnościowe, inwestycje, analityka finansowa, import Excel, integracje bankowe. Dane przykładowe z PRD nie są automatycznie danymi startowymi.

## Wymagania funkcjonalne

### FR-01: Konta i logowanie
- Opis: Użytkownik loguje się do własnego konta i może zakończyć sesję.
- Kryteria: poprawne dane umożliwiają wejście; błędne nie tworzą sesji; wylogowanie odbiera dostęp do chronionych operacji; dostęp bez logowania jest odrzucany przez backend.
- Pierwsze konto powstaje podczas konfiguracji; po jego utworzeniu konfiguracja nie może służyć do tworzenia kolejnych kont. Kolejne konta powstają przez zaproszenia z kopiowanym linkiem, bez e-maili (decyzja użytkownika).
- Uzgodnienie: odzyskiwanie konta realizuje operator lokalnej instalacji według opisanej procedury.
- Priorytet: Must. Źródło: PRD 4, 57, 64.

### FR-02: Utworzenie gospodarstwa
- Opis: Zalogowany użytkownik może utworzyć gospodarstwo.
- Kryteria: nowe gospodarstwo pojawia się na liście dostępnej twórcy; posiada domyślną walutę PLN; dane pozostają dostępne po ponownym zalogowaniu.
- Uzgodnione doprecyzowanie: twórca otrzymuje rolę Owner; zapis gospodarstwa i członkostwa odbywa się atomowo.
- Priorytet: Must. Źródło: PRD 5.1, 5.2, 59.

### FR-03: Wiele gospodarstw i izolacja
- Opis: Użytkownik może należeć do wielu gospodarstw i przełączać kontekst.
- Kryteria: lista obejmuje tylko gospodarstwa użytkownika; zmiana aktywnego gospodarstwa zmienia listy członków i dochodów; ręczna zmiana identyfikatora w żądaniu nie ujawnia danych obcego gospodarstwa; powiązanie źródła dochodu z członkiem obcego gospodarstwa jest odrzucane.
- Priorytet: Must. Źródło: PRD 5.1, 58; BR-01, BR-03.

### FR-04: Dołączenie użytkownika
- Opis: Użytkownik może zostać zaproszony do istniejącego gospodarstwa.
- Kryteria: przyjęcie poprawnego zaproszenia tworzy członkostwo z przypisaną rolą; zaproszenie do jednego gospodarstwa nie daje dostępu do innego.
- Zaproszenie przekazywane jest kopiowanym linkiem, bez e-maila. Osoba bez konta może utworzyć je podczas przyjęcia zaproszenia; istniejący użytkownik loguje się i dołącza do gospodarstwa.
- Uzgodnione kryteria: link jednorazowy, ważny 7 dni, możliwy do odwołania; zużyty, odwołany i wygasły link nie tworzą członkostwa. Ponowne przyjęcie nie dubluje członkostwa.
- Link otwierany jest na komputerze hostującym aplikację; localhost nie umożliwia wejścia z innego urządzenia.
- Priorytet: Must. Źródło: PRD 5.1.

### FR-05: Role aplikacyjne
- Opis: Członkostwo użytkownika posiada rolę Owner, Administrator, Member albo Viewer, niezależną od relacji rodzinnej.
- Kryteria: Owner ma pełną kontrolę w gospodarstwie; Administrator zarządza członkami; Viewer nie wykonuje operacji zmieniających dane ani przez UI, ani przez API; użytkownik może mieć różne role w różnych gospodarstwach.
- Member ma wyłącznie odczyt członków i źródeł dochodu. Edycja tych danych dostępna jest dla Owner i Administrator (decyzja użytkownika).
- Uzgodnione doprecyzowanie: tylko Owner zarządza zaproszeniami i rolami; nie można usunąć ani zdegradować ostatniego Owner. Granice opisuje decision-proposals.md.
- Priorytet: Must. Źródło: PRD 5.2.

### FR-06: Członkowie gospodarstwa
- Opis: Uprawniony użytkownik dodaje i edytuje członków niezależnie od kont logowania.
- Kryteria: można dodać członka bez konta; można powiązać konto z odpowiadającym mu członkiem; członek bez dochodów jest poprawny; brak konta nie blokuje przypisania źródła dochodu.
- Usunięcie lub dezaktywacja nie może niszczyć powiązanej historii finansowej.
- Priorytet: Must. Źródło: PRD 4, 6, 50.

### FR-07: Relacje rodzinne
- Opis: Typy relacji rodzinnych są konfigurowalne.
- Kryteria: można zdefiniować typ i przypisać go członkowi; zmiana relacji rodzinnej nie zmienia roli aplikacyjnej.
- Uzgodnione doprecyzowanie: słownik typów jest własnością gospodarstwa, aby jego edycja nie zmieniała innych gospodarstw.
- Priorytet: Must. Źródło: PRD 5.3.

### FR-08: Źródła dochodu
- Opis: Źródło należy do gospodarstwa i jest przypisane bezpośrednio do niego albo do jego członka.
- Kryteria: przechowywane są nazwa, typ, podmiot wypłacający, daty początku i opcjonalnego końca, domyślna kwota miesięczna, waluta, częstotliwość, regularność, opis i status; członek może mieć zero lub wiele źródeł; dostępne są dodawanie, edycja i dezaktywacja według uprawnień; kwota zachowuje precyzję dziesiętną.
- Nazwa świadczenia jest danymi użytkownika, nie stałą regułą programu.
- Kwota domyślna nie tworzy miesięcznego przychodu ani transakcji. Ich obsługa jest częścią kolejnych etapów.
- Priorytet: Must. Źródło: PRD 6, 59–60.

### FR-09: Audyt i historia
- Opis: Istotne zmiany dotyczące danych fundamentu pozostawiają ślad.
- Kryteria: zmiana źródła dochodu zapisuje wykonawcę, czas, obiekt i wartości przed/po; archiwizacja zachowuje dane historyczne; zdarzenia logowania są rejestrowane zgodnie ze standardem bezpieczeństwa.
- Szczegółowy zakres zdarzeń i retencja do ustalenia przy projektowaniu.
- Priorytet: Must. Źródło: PRD 49–50, 57.

## Wymagania niefunkcjonalne
Standardy projektowe obowiązują przez odwołanie do ../../standards/; poniżej ich zastosowanie do fundamentu.

### NFR-01: Testowalna kontrola dostępu
- Dla każdej operacji zapisu sprawdzić brak logowania, Viewer i użytkownika spoza gospodarstwa.
- Dla odczytu sprawdzić bezpośrednie odwołanie do identyfikatora obcego gospodarstwa i jego zasobów.
- Oczekiwany wynik: odmowa dostępu bez ujawnienia danych i bez zmiany stanu.
- Priorytet: Must.

### NFR-02: Trwałość lokalnego MVP
- Po utworzeniu gospodarstwa, członka i źródła dochodu odtworzenie kontenerów bez usuwania wolumenów zachowuje te obiekty.
- Uruchomienie na pustych wolumenach pozwala przejść konfigurację i utworzyć pierwsze konto.
- Priorytet: Must. Szczegóły: ../../operations/local-deployment.md.

### NFR-03: Integralność danych fundamentu
- Błąd tworzenia członkostwa wycofuje tworzenie gospodarstwa.
- Nie można zapisać źródła powiązanego z członkiem innego gospodarstwa.
- Kwoty zapisane i odczytane zachowują wartość dziesiętną.
- Priorytet: Must.

## Scenariusz odbioru
1. Uruchomić pustą instalację lokalną i utworzyć pierwsze konto.
2. Utworzyć dwa gospodarstwa; dodać członka bez konta.
3. Dodać po dwa źródła dochodu: członka i gospodarstwa.
4. Dołączyć drugiego użytkownika, nadać Viewer i sprawdzić odmowę zapisu.
5. Przełączyć gospodarstwo i sprawdzić rozdzielenie danych.
6. Odtworzyć kontenery, zalogować się i potwierdzić trwałość danych.

## Uzgodnienia
- Q-01: rozstrzygnięte — pierwsze konto podczas konfiguracji, kolejne przez kopiowany link zaproszenia, bez e-maili.
- Q-02: rozstrzygnięte — Member tylko odczyt; edycja członków i źródeł dochodu przez Owner/Administrator.
- Zatwierdzono jako część tego zakresu: ważność linku 7 dni, zarządzanie zaproszeniami i rolami przez Owner, ochrona ostatniego Owner, odzyskiwanie dostępu przez operatora, twórca jako Owner i lokalne słowniki relacji.
- Techniczne wybory i macierz: decision-proposals.md.
