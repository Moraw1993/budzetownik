# Product Requirements Document

## 1. Informacje ogólne

### 1.1. Nazwa robocza produktu

**Domowe Finanse / Household Finance Manager**

### 1.2. Cel produktu

Celem projektu jest stworzenie nowoczesnej aplikacji webowej umożliwiającej kompleksowe zarządzanie finansami gospodarstwa domowego w czterech głównych obszarach:

1. miesięczne rozdysponowanie budżetu,
2. zarządzanie kredytami i harmonogramami ich spłat,
3. zarządzanie oszczędnościami i inwestycjami,
4. analityka finansowa gospodarstwa domowego.

Aplikacja ma zastąpić obecnie wykorzystywane arkusze Excel oraz przygotować fundament pod dalszą rozbudowę systemu, w szczególności o:

* rzeczywistą ewidencję wydatków,
* integrację z rachunkami bankowymi,
* automatyczną synchronizację transakcji,
* prognozowanie finansowe,
* zarządzanie majątkiem gospodarstwa domowego.

---

# 2. Problem biznesowy

Obecny proces zarządzania finansami realizowany jest głównie za pomocą arkuszy Excel.

Rozwiązanie to pozwala przechowywać dane, ale posiada szereg ograniczeń:

* brak centralnego modelu gospodarstwa domowego,
* brak relacji między członkami rodziny, dochodami, kredytami i oszczędnościami,
* brak wygodnej historii zmian,
* brak automatycznego generowania harmonogramów,
* brak mechanizmów kontroli poprawności danych,
* brak wygodnej analityki,
* brak wersjonowania i audytu zmian,
* trudne przeglądanie danych historycznych,
* ograniczona możliwość rozwoju systemu,
* ryzyko przypadkowego usunięcia lub nadpisania danych.

Nowa aplikacja powinna stanowić jedno źródło informacji o finansach gospodarstwa domowego.

---

# 3. Zakres produktu

System zostanie podzielony na następujące moduły:

1. **Gospodarstwo domowe i użytkownicy**
2. **Rozdysponowanie budżetu**
3. **Kredyty**
4. **Oszczędności i inwestycje**
5. **Analityka**

W przyszłości:

6. **Wydatki i transakcje**
7. **Integracje bankowe**
8. **Prognozowanie finansowe**
9. **Majątek gospodarstwa domowego**

---

# 4. Model użytkownika i gospodarstwa domowego

## 4.1. Rozdzielenie użytkownika od członka rodziny

System musi rozróżniać dwa podstawowe pojęcia.

### Użytkownik

Osoba posiadająca konto umożliwiające logowanie do aplikacji.

Przykład:

* Arek posiada login i hasło,
* Dominika posiada własny login.

### Członek gospodarstwa

Osoba należąca do gospodarstwa domowego.

Przykład:

* Arek,
* Dominika,
* dziecko.

Członek gospodarstwa **nie musi posiadać konta użytkownika**.

Dzięki temu możliwe będzie reprezentowanie:

* dzieci,
* osób starszych,
* osób niekorzystających z aplikacji.

Użytkownik może zostać powiązany z odpowiadającym mu członkiem gospodarstwa.

---

# 5. Gospodarstwo domowe

## 5.1. Tworzenie gospodarstwa

Po pierwszym zalogowaniu użytkownik:

* może utworzyć nowe gospodarstwo domowe,
* może zostać zaproszony do istniejącego gospodarstwa.

Użytkownik może należeć do jednego lub wielu gospodarstw domowych.

Przykład:

> Arek może posiadać gospodarstwo „Rodzina Andrzejczyków” oraz dodatkowo gospodarstwo wykorzystywane do zarządzania finansami rodziców.

---

## 5.2. Role aplikacyjne

W ramach gospodarstwa powinny istnieć co najmniej role:

### Owner

Pełna kontrola nad gospodarstwem.

### Administrator

Może zarządzać:

* członkami,
* budżetem,
* kredytami,
* oszczędnościami.

### Member

Może korzystać z wybranych funkcji finansowych.

### Viewer

Dostęp tylko do odczytu.

Role aplikacyjne nie są tym samym co role rodzinne.

---

## 5.3. Role rodzinne

Członek gospodarstwa może posiadać typ relacji, np.:

* rodzic,
* małżonek/partner,
* dziecko,
* inny członek gospodarstwa.

Typy powinny być konfigurowalne.

---

# 6. Dochody

Każdy członek gospodarstwa może posiadać:

* 0 źródeł dochodu,
* 1 źródło dochodu,
* wiele źródeł dochodu.

Źródło dochodu może być również przypisane bezpośrednio do gospodarstwa.

## 6.1. Przykładowe źródła dochodu

* umowa o pracę,
* umowa zlecenie,
* umowa o dzieło,
* działalność gospodarcza,
* świadczenie społeczne,
* świadczenie na dziecko,
* emerytura,
* renta,
* najem,
* odsetki,
* dywidendy,
* premie,
* inne.

System nie powinien hardkodować nazwy konkretnego świadczenia, np. „800+”.

Powinna istnieć ogólna kategoria:

> świadczenie rodzinne / świadczenie na dziecko

oraz możliwość określenia jego nazwy.

---

## 6.2. Źródło dochodu

Obiekt `IncomeSource` powinien zawierać m.in.:

* właściciela źródła,
* nazwę,
* typ,
* podmiot wypłacający,
* datę rozpoczęcia,
* opcjonalną datę zakończenia,
* domyślną miesięczną kwotę,
* walutę,
* częstotliwość,
* informację czy dochód jest regularny,
* opis,
* status aktywny/nieaktywny.

Kwota wykorzystana w konkretnym miesiącu może różnić się od wartości domyślnej.

---

# 7. Moduł 1 — Rozdysponowanie budżetu

## 7.1. AS-IS

Źródło:

[rozdysponowanie-budzetu.xlsx](../source-materials/rozdysponowanie-budzetu.xlsx)

Obecnie:

* każdy arkusz reprezentuje rok,
* kolumny reprezentują miesiące,
* wiersze reprezentują strukturę budżetu,
* użytkownicy ręcznie wprowadzają przychody,
* następnie przypisują dostępne środki do odpowiednich celów budżetowych.

Arkusz służy wyłącznie do **planowania i rozdysponowania środków**.

Nie reprezentuje:

* salda rachunków bankowych,
* rzeczywistych transakcji,
* rzeczywistych wydatków.

Ta separacja musi zostać zachowana w pierwszej wersji aplikacji.

---

# 8. Koncepcja budżetu

Budżet będzie posiadał następującą hierarchię:

```text
Rok budżetowy
    ↓
Miesiąc budżetowy
    ↓
Grupa
    ↓
Kategoria
    ↓
Element
```

Przykład:

```text
Wydatki
└── Mieszkanie
    ├── Czynsz
    ├── Energia elektryczna
    └── Subskrypcje
        ├── Netflix
        ├── OneDrive
        └── ChatGPT
```

Element będzie poziomem opcjonalnym.

Jeżeli kategoria nie posiada elementów:

```text
Mieszkanie
└── Czynsz
```

kategoria sama reprezentuje końcową pozycję budżetową.

Nie należy tworzyć sztucznego elementu:

```text
Czynsz
└── Czynsz
```

---

# 9. Rok budżetowy

Użytkownik będzie mógł:

* utworzyć rok budżetowy,
* zmienić jego nazwę,
* dodać opis,
* przeglądać miesiące,
* archiwizować rok.

Przykład:

> Budżet 2027

Rok nie musi odpowiadać rokowi kalendarzowemu, dzięki czemu architektura pozostanie elastyczna.

---

# 10. Miesiąc budżetowy

## 10.1. Tworzenie

Użytkownik będzie mógł utworzyć miesiąc, np.:

> Wrzesień 2026

Kreator powinien umożliwić:

* wybór miesiąca,
* dodanie opisu,
* wybór szablonu,
* skopiowanie struktury z poprzedniego miesiąca,
* skopiowanie struktury z dowolnego miesiąca,
* skopiowanie struktury z poprzedniego roku,
* ręczne przygotowanie struktury.

Jeżeli użytkownik nie wybierze żadnego wariantu, system utworzy podstawowy szablon.

---

## 10.2. Import struktury

Importowane będą:

* grupy,
* kategorie,
* elementy,
* kolejność.

Domyślnie **nie będą importowane wartości finansowe**.

Przykład:

```text
Netflix                0 zł
Czynsz                  0 zł
Energia elektryczna     0 zł
```

Opcjonalnie w przyszłości system może umożliwiać:

> „Skopiuj również wartości z poprzedniego miesiąca”.

---

# 11. Status miesiąca

Miesiąc powinien posiadać stan:

### DRAFT

Miesiąc został utworzony, ale planowanie jeszcze się nie rozpoczęło.

### OPEN

Budżet jest aktualnie przygotowywany lub wykorzystywany.

### CLOSED

Budżet został zakończony i nie powinien być przypadkowo zmieniany.

### ARCHIVED

Miesiąc historyczny.

Zmiana danych w zamkniętym miesiącu powinna wymagać wcześniejszego ponownego otwarcia.

---

# 12. Widok roku budżetowego

Widok roku powinien prezentować miesiące jako karty.

Przykład:

```text
┌─────────────────────────────┐
│ WRZESIEŃ 2026               │
│                             │
│ Przychody:       14 200 zł  │
│ Rozdysponowano:  13 900 zł  │
│ Pozostało:          300 zł  │
│                             │
│ ● OTWARTY                    │
└─────────────────────────────┘
```

Karta powinna zawierać:

* nazwę miesiąca,
* status,
* sumę przychodów,
* rozdysponowaną wartość,
* nierozdysponowaną wartość,
* opcjonalny komentarz.

---

# 13. Widok miesiąca

Widok powinien składać się co najmniej z:

## Sekcji A — Podsumowanie

```text
Przychody        14 200 zł
Rozdysponowano   13 900 zł
Pozostało           300 zł
```

Podstawowa zależność:

```text
pozostało =
suma przychodów
-
suma rozdysponowanych środków
```

System powinien ostrzegać, jeżeli:

```text
rozdysponowano > przychody
```

---

## Sekcji B — Przychody

Przykład:

| Osoba    | Źródło        |    Kwota |
| -------- | ------------- | -------: |
| Arek     | Wynagrodzenie | 8 500 zł |
| Dominika | Wynagrodzenie | 4 900 zł |
| Dziecko  | Świadczenie   |   800 zł |

oraz:

| Gospodarstwo | Źródło  |  Kwota |
| ------------ | ------- | -----: |
| Rodzina      | Odsetki | 120 zł |

Kliknięcie wartości powinno otworzyć formularz edycji.

---

# 14. Dodawanie przychodu

Użytkownik wybiera:

1. właściciela:

   * członka rodziny,
   * gospodarstwo,

2. źródło dochodu,

3. kwotę,

4. datę lub miesiąc przypisania,

5. opcjonalny komentarz.

Powinna istnieć również możliwość utworzenia jednorazowego przychodu.

---

# 15. Rozdysponowanie środków

Druga część miesiąca reprezentuje plan przeznaczenia pieniędzy.

Przykład:

```text
MIESZKANIE
───────────────────────
Czynsz         1 200 zł
Prąd             230 zł
Gaz              150 zł

SUBSKRYPCJE
───────────────────────
Netflix           67 zł
OneDrive          43 zł
ChatGPT          100 zł
```

Każda wartość będzie edytowalna inline lub za pomocą małego formularza/modalu.

---

# 16. Historia pozycji

Po wskazaniu kategorii lub elementu użytkownik powinien zobaczyć historię.

Przykład:

```text
Netflix

Maj        60 zł
Czerwiec   60 zł
Lipiec     67 zł
Sierpień   67 zł
Wrzesień   67 zł
```

Opcjonalnie:

```text
Średnia z 6 miesięcy: 64,67 zł
Zmiana m/m: 0%
```

Historia nie powinna utrudniać podstawowego procesu planowania.

---

# 17. Edycja struktury budżetu

Użytkownik będzie mógł:

* dodawać grupy,
* dodawać kategorie,
* dodawać elementy,
* zmieniać nazwy,
* zmieniać kolejność,
* przeciągać elementy metodą drag & drop,
* przenosić kategorię pomiędzy grupami,
* usuwać elementy.

Usunięcie obiektu posiadającego dane finansowe musi wymagać dodatkowego potwierdzenia.

Przykład:

> Kategoria „Netflix” zawiera dane historyczne. Czy na pewno chcesz ją usunąć z bieżącego miesiąca?

Preferowane rozwiązanie:

**usunięcie ze struktury miesiąca nie usuwa historii.**

---

# 18. Szablony budżetu

System powinien umożliwiać utworzenie szablonu budżetu.

Przykład:

> „Standardowy budżet rodzinny”

który może zawierać strukturę:

```text
Mieszkanie
Transport
Żywność
Dziecko
Subskrypcje
Kredyty
Oszczędności
Inwestycje
Rezerwa
```

Szablon będzie można wykorzystać podczas tworzenia kolejnych miesięcy.

---

# 19. Ważna reguła modułu budżetowego

Moduł 1 będzie reprezentował:

> **plan przeznaczenia pieniędzy**

a nie:

> **rzeczywiste wykonanie budżetu**.

Przykład:

```text
Plan:
Żywność → 1 500 zł
```

nie oznacza:

```text
Na koncie wydano dokładnie 1 500 zł.
```

Dopiero przyszły moduł wydatków będzie umożliwiał porównanie:

```text
PLAN      1 500 zł
WYKONANIE 1 327 zł
RÓŻNICA     173 zł
```

---

# 20. Moduł 2 — Kredyty

## 20.1. AS-IS

Źródło:

[splaty-kredytu.xlsx](../source-materials/splaty-kredytu.xlsx)

z wyłączeniem zakładki dotyczącej przelewów VeloBank.

---

# 21. Typy kredytów

System powinien przygotować model pozwalający obsłużyć m.in.:

* kredyt ratalny,
* kredyt gotówkowy,
* kredyt samochodowy,
* kredyt hipoteczny,
* pożyczkę,
* inne zobowiązanie.

MVP może koncentrować się na kredytach ratalnych, ale model danych nie powinien tego ograniczać.

---

# 22. Dodanie kredytu

Użytkownik wybiera:

* gospodarstwo,
* właściciela/właścicieli zobowiązania,
* bank lub instytucję,
* typ kredytu.

Kredyt może należeć do:

* jednej osoby,
* kilku współkredytobiorców,
* gospodarstwa.

---

# 23. Dane kredytu

System powinien przechowywać co najmniej:

### Identyfikacja

* nazwa kredytu,
* numer umowy,
* numer wniosku — opcjonalnie,
* bank,
* typ kredytu,
* opis.

### Daty

* data zawarcia umowy,
* data uruchomienia,
* termin pierwszej raty,
* planowana data ostatniej raty.

### Finansowanie

* kwota kapitału,
* waluta,
* liczba rat,
* kwota całkowita do spłaty,
* miesięczna rata,
* wysokość ostatniej raty korygującej.

### Oprocentowanie

* oprocentowanie nominalne,
* stałe/zmienne,
* RRSO — jeżeli dostępne,
* marża,
* stopa referencyjna — jeżeli dotyczy.

### Koszty

* prowizja,
* ubezpieczenie,
* opłata przygotowawcza,
* inne opłaty.

### Rachunki

* rachunek do spłaty,
* rachunek do nadpłat,
* tytuł przelewu,
* identyfikator klienta — opcjonalnie.

### Przedmiot finansowania

* nazwa,
* opis,
* cena,
* sprzedawca — opcjonalnie.

Kredyt może posiadać wiele przedmiotów finansowania.

---

# 24. Harmonogram spłat

Na podstawie parametrów system będzie mógł wygenerować harmonogram.

Przykład:

| Rata | Termin     | Kapitał | Odsetki | Opłaty | Rata | Pozostały kapitał |
| ---: | ---------- | ------: | ------: | -----: | ---: | ----------------: |
|    1 | 10.10.2026 |     ... |     ... |    ... |  ... |               ... |
|    2 | 10.11.2026 |     ... |     ... |    ... |  ... |               ... |

Model powinien obsługiwać:

* raty równe,
* raty malejące,
* harmonogram wprowadzony ręcznie.

---

# 25. Harmonogram bankowy jako źródło nadrzędne

Jeżeli użytkownik posiada oficjalny harmonogram bankowy, powinien mieć możliwość:

* ręcznego wprowadzenia harmonogramu,
* edycji wygenerowanego harmonogramu,
* w przyszłości importu CSV/XLSX/PDF.

Harmonogram bankowy może zostać oznaczony jako:

> **harmonogram referencyjny**

i posiadać pierwszeństwo przed harmonogramem obliczonym przez aplikację.

---

# 26. Spłaty kredytu

Użytkownik będzie mógł rejestrować płatność.

Płatność powinna posiadać:

* kredyt,
* datę płatności,
* ratę, której dotyczy,
* kwotę,
* rachunek docelowy,
* typ:

  * rata,
  * nadpłata,
  * opłata,
* opis.

Opcjonalnie:

* część kapitałowa,
* część odsetkowa,
* opłaty.

---

# 27. Status rat

Rata może posiadać stan:

```text
PLANNED
PARTIALLY_PAID
PAID
OVERDUE
CANCELLED
```

Aplikacja powinna automatycznie wskazywać:

* najbliższą ratę,
* raty opłacone,
* zaległości,
* pozostałą liczbę rat.

---

# 28. Nadpłaty

Użytkownik będzie mógł dodać nadpłatę.

System powinien pozwolić wskazać sposób jej rozliczenia:

### Skrócenie okresu

Rata pozostaje podobna, ale zmniejsza się liczba rat.

### Obniżenie raty

Okres pozostaje podobny, ale zmniejsza się wysokość przyszłych rat.

Jeżeli bank stosuje inne zasady, użytkownik powinien mieć możliwość ręcznej korekty harmonogramu.

Każde przeliczenie harmonogramu powinno zachowywać poprzednią wersję.

---

# 29. Załączniki

Do kredytu będzie można dodać:

* umowę,
* harmonogram,
* aneks,
* potwierdzenie nadpłaty,
* zaświadczenie o spłacie,
* inne dokumenty.

Pliki powinny posiadać:

* nazwę,
* typ,
* datę dodania,
* opis.

---

# 30. Status kredytu

Kredyt może posiadać stan:

```text
DRAFT
ACTIVE
PAID
CLOSED
REFINANCED
ARCHIVED
```

Zamknięcie kredytu nie powoduje usunięcia danych.

Kredyt przechodzi do historii.

---

# 31. Dashboard kredytu

Przykład:

```text
Laptop — kredyt ratalny

Bank:                  XYZ
Kwota początkowa:      6 000 zł
Spłacono:              3 250 zł
Pozostało:             2 750 zł

Raty:
14 / 24

Najbliższa rata:
10.10.2026
250 zł

Postęp:
████████████░░░░░░░ 54%
```

---

# 32. Moduł 3 — Oszczędności i inwestycje

## 32.1. AS-IS

Źródło:

[splaty-kredytu.xlsx](../source-materials/splaty-kredytu.xlsx)

Zakładka:

> VeloBank — przelewy

---

# 33. Obiekt finansowy

System powinien umożliwiać utworzenie różnych typów obiektów:

### Oszczędnościowe

* konto oszczędnościowe,
* lokata,
* gotówka,
* inne.

### Inwestycyjne

* rachunek maklerski,
* akcje,
* ETF,
* obligacje,
* fundusze,
* inne aktywa.

---

# 34. Konto oszczędnościowe

Podstawowe dane:

* nazwa,
* właściciel,
* bank,
* numer rachunku — opcjonalny,
* waluta,
* data otwarcia,
* oprocentowanie,
* opis.

Użytkownik będzie mógł rejestrować:

* wpłatę,
* wypłatę,
* odsetki,
* opłatę,
* korektę.

---

# 35. Saldo

Saldo powinno być wyliczane przede wszystkim na podstawie transakcji:

```text
saldo =
saldo początkowe
+ wpłaty
+ odsetki
- wypłaty
- opłaty
± korekty
```

Nie należy pozwalać na cichą zmianę salda.

Opcja:

> „Skoryguj saldo”

powinna tworzyć transakcję typu `ADJUSTMENT`.

Pozwala to zachować pełną historię zmian.

---

# 36. Cele oszczędnościowe

Użytkownik będzie mógł utworzyć cel.

Przykład:

```text
Wakacje
Cel: 12 000 zł
Termin: 01.06.2027
```

Cel powinien posiadać:

* nazwę,
* docelową kwotę,
* aktualną kwotę,
* termin,
* priorytet,
* opis,
* status.

Przykład wizualizacji:

```text
Wakacje

8 200 / 12 000 zł

██████████████░░░░░ 68%
```

---

# 37. Wirtualna alokacja środków

Jedno konto bankowe może finansować kilka celów.

Przykład:

```text
Konto oszczędnościowe
Saldo: 40 000 zł

Fundusz awaryjny:   20 000 zł
Wakacje:             8 000 zł
Samochód:             7 000 zł
Nieprzypisane:        5 000 zł
```

Cele nie będą osobnymi rachunkami bankowymi, lecz logiczną alokacją środków.

System musi zapobiegać podwójnemu liczeniu tych samych pieniędzy.

---

# 38. Konto inwestycyjne

Rachunek inwestycyjny powinien umożliwiać przechowywanie:

* wpłat,
* wypłat,
* zakupów,
* sprzedaży,
* dywidend,
* odsetek,
* prowizji.

Transakcja zakupu powinna zawierać m.in.:

* instrument,
* datę,
* liczbę jednostek,
* cenę,
* prowizję,
* walutę.

---

# 39. Instrumenty finansowe

Model powinien umożliwiać obsługę:

```text
STOCK
ETF
BOND
TREASURY_BOND
FUND
OTHER
```

Instrument może posiadać:

* nazwę,
* symbol,
* ISIN,
* walutę,
* emitenta,
* typ.

---

# 40. Obligacje Skarbu Państwa

System powinien umożliwiać utworzenie inwestycji w obligacje skarbowe.

Użytkownik wybiera:

* serię,
* typ obligacji,
* datę zakupu,
* liczbę obligacji,
* cenę jednostkową,
* wartość inwestycji.

Warunki konkretnej emisji powinny być przechowywane jako dane, a nie zakodowane bezpośrednio w kodzie aplikacji.

Przykładowy model:

```text
Rok 1:
oprocentowanie stałe

Rok 2+:
CPI + marża
```

System powinien przechowywać:

* sposób oprocentowania,
* okres kapitalizacji,
* marżę,
* dane inflacyjne wykorzystane do obliczenia,
* daty kolejnych okresów odsetkowych.

---

# 41. Zewnętrzne dane dla obligacji

Integracja z zewnętrznym źródłem danych powinna być traktowana jako funkcjonalność rozszerzona.

Jeżeli dostępne będzie stabilne źródło danych, system może automatycznie pobierać:

* parametry nowych emisji,
* oprocentowanie pierwszego okresu,
* marże,
* CPI wykorzystywane przy indeksacji.

System musi jednak umożliwiać ręczne wprowadzenie tych danych.

Nie należy uzależniać podstawowego działania aplikacji od zewnętrznego API.

---

# 42. Moduł 4 — Analityka

Moduł analityczny powinien agregować informacje ze wszystkich pozostałych modułów.

---

# 43. Dashboard główny

Dashboard powinien prezentować m.in.:

### Finanse gospodarstwa

```text
Przychody miesięczne
Rozdysponowany budżet
Nierozdysponowane środki
Łączne oszczędności
Łączne inwestycje
Łączne zobowiązania
```

---

# 44. Analityka budżetu

Przykładowe wskaźniki:

* dochód gospodarstwa miesiąc do miesiąca,
* struktura rozdysponowania pieniędzy,
* udział kategorii w budżecie,
* trend kategorii,
* średnia wartość kategorii,
* oszczędności planowane,
* udział oszczędności w przychodach.

---

# 45. Analityka kredytów

Wskaźniki:

* całkowita wartość zobowiązań,
* pozostały kapitał,
* miesięczne obciążenie ratami,
* liczba aktywnych kredytów,
* suma zapłaconych odsetek,
* suma kosztów kredytowych,
* suma nadpłat,
* przewidywany termin spłaty.

Przykładowy KPI:

```text
Debt Service Ratio =
miesięczne raty / miesięczne dochody
```

---

# 46. Analityka oszczędności

Wskaźniki:

* całkowite oszczędności,
* zmiana miesiąc do miesiąca,
* struktura oszczędności,
* postęp celów,
* średnia miesięczna wpłata,
* wartość środków nieprzypisanych do celów.

---

# 47. Analityka inwestycji

W późniejszym etapie:

* wartość portfela,
* wartość wpłat,
* wartość bieżąca,
* wynik nominalny,
* stopa zwrotu,
* struktura aktywów,
* struktura według waluty,
* struktura według klasy aktywów.

---

# 48. Net Worth

Docelowo aplikacja powinna prezentować wartość netto gospodarstwa.

```text
NET WORTH =
AKTYWA
-
ZOBOWIĄZANIA
```

Przykład:

```text
Oszczędności       80 000 zł
Inwestycje         55 000 zł
--------------------------------
Aktywa            135 000 zł

Kredyty            25 000 zł
--------------------------------
Net Worth         110 000 zł
```

---

# 49. Historia i audyt

Każda istotna operacja finansowa powinna posiadać informacje:

* kto wykonał zmianę,
* kiedy,
* jaki obiekt został zmieniony,
* wartość poprzednią,
* wartość nową.

Szczególnie dotyczy to:

* kredytów,
* harmonogramów,
* spłat,
* transakcji,
* korekt salda,
* budżetów zamkniętych.

---

# 50. Usuwanie danych

Dane finansowe nie powinny być bezpowrotnie usuwane bez uzasadnienia.

Preferowane mechanizmy:

* archiwizacja,
* soft delete,
* oznaczenie jako nieaktywne.

Dla operacji destrukcyjnych:

```text
Czy na pewno chcesz usunąć ten element?

[Anuluj] [Usuń]
```

Dla szczególnie istotnych danych może być wymagane dodatkowe wpisanie potwierdzenia.

---

# 51. UX/UI

Aplikacja powinna być zaprojektowana jako nowoczesny dashboard finansowy.

## Desktop-first

Pierwsza wersja będzie zoptymalizowana przede wszystkim pod komputery.

Interfejs musi jednak być responsywny.

---

## 51.1. Główna nawigacja

Przykład:

```text
Dashboard
Budżet
Kredyty
Oszczędności
Inwestycje
Analityka
Gospodarstwo
Ustawienia
```

---

# 52. Dashboard startowy

Po zalogowaniu użytkownik powinien zobaczyć m.in.:

```text
Dzień dobry, Arek

Budżet — wrzesień 2026
14 200 zł przychodów
13 900 zł rozdysponowano
300 zł pozostało

Kredyty
3 aktywne
2 150 zł najbliższych rat

Oszczędności
87 400 zł

Cele
Wakacje         68%
Fundusz awaryjny 100%
Samochód        35%
```

---

# 53. Nawigacja kontekstowa

Przejście:

```text
Budżet
→ 2026
→ Wrzesień
```

powinno być zawsze widoczne jako breadcrumb.

Przykład:

```text
Budżet / 2026 / Wrzesień
```

Użytkownik powinien móc łatwo powrócić do widoku roku.

---

# 54. Wymagania techniczne

## Backend

Preferowany:

```text
Python
Django
Django ORM
Django migrations
```

---

## Baza danych

```text
PostgreSQL
```

PostgreSQL będzie głównym źródłem prawdy dla danych aplikacyjnych.

---

## Frontend

Rekomendowany:

```text
TypeScript
React
Next.js
```

Alternatywnie:

```text
React + Vite
```

UI:

* Tailwind CSS,
* shadcn/ui,
* Recharts lub Apache ECharts,
* Lucide Icons.

---

## Uruchamianie MVP

MVP działa lokalnie na komputerze użytkownika, w kontenerach Docker zarządzanych przez Docker Compose.
Frontend React/TypeScript, backend Django i PostgreSQL są uruchamiane jako usługi jednego projektu Compose.
Dostęp do aplikacji odbywa się z przeglądarki na tym samym komputerze przez localhost. Opublikowane porty aplikacji należy wiązać z 127.0.0.1; baza danych działa w wewnętrznej sieci kontenerów.
Dane PostgreSQL i załączniki muszą korzystać z trwałych wolumenów, zachowujących zawartość po restarcie i odtworzeniu kontenerów. Trwały wolumen nie zastępuje kopii zapasowej.
Załączniki MVP są przechowywane w filesystemie na trwałym wolumenie; metadane pozostają w PostgreSQL.
Docelowy sposób uruchomienia: docker compose up --build. Instrukcja wdrożenia musi obejmować konfigurację, migracje Django, utworzenie pierwszego użytkownika oraz wykonanie i odtworzenie kopii danych i załączników.
Konfiguracja lokalna i sekrety są przekazywane przez zmienne środowiskowe; repozytorium zawiera jedynie przykładowe wartości.
Hosting publiczny i dostęp z sieci domowej pozostają poza zakresem lokalnego MVP.
Wymaganie HTTPS z PRD pozostaje aktualne; sposób obsługi lokalnego certyfikatu zostanie określony w projekcie wdrożenia.

---

# 55. Przechowywanie dokumentów

Załączników nie należy przechowywać bezpośrednio jako duże obiekty w podstawowych tabelach PostgreSQL.

Preferowana architektura:

```text
PostgreSQL
    ↓
metadata dokumentu

Object Storage
    ↓
plik
```

Dla lokalnego MVP można wykorzystać filesystem.

Docelowo:

* S3,
* MinIO,
* kompatybilny Object Storage.

---

# 56. Architektura aplikacji

Na początek rekomendowana jest architektura:

> **modularny monolit**

z wyraźnie rozdzielonymi domenami:

```text
app/
├── auth/
├── households/
├── members/
├── income/
├── budgets/
├── loans/
├── savings/
├── investments/
├── analytics/
├── attachments/
└── audit/
```

Nie ma potrzeby stosowania mikroserwisów w pierwszej wersji.

---

# 57. Bezpieczeństwo

Ponieważ aplikacja przechowuje szczególnie istotne informacje finansowe, wymagane są:

* bezpieczne haszowanie haseł,
* HTTPS,
* kontrola dostępu na poziomie gospodarstwa,
* izolacja danych gospodarstw,
* zabezpieczenie endpointów,
* CSRF/XSS protection odpowiednio do sposobu autoryzacji,
* limity prób logowania,
* bezpieczne zarządzanie sesją,
* logowanie zdarzeń bezpieczeństwa.

Opcjonalnie:

* MFA/TOTP.

---

# 58. Izolacja danych

Każdy obiekt biznesowy musi być jednoznacznie przypisany do gospodarstwa.

Przykładowo:

```text
household_id
```

powinien znajdować się bezpośrednio lub pośrednio w każdym obiekcie finansowym.

Backend musi weryfikować dostęp niezależnie od frontendowego interfejsu.

Nie wolno polegać wyłącznie na ukrywaniu danych w UI.

---

# 59. Waluty

System powinien od początku posiadać typ `currency`.

Domyślna waluta gospodarstwa:

```text
PLN
```

ale model danych nie powinien blokować:

* EUR,
* USD,
* GBP,
* innych walut.

Automatyczne przeliczenia kursowe mogą zostać dodane później.

---

# 60. Precyzja danych finansowych

Kwoty finansowe nie mogą być przechowywane jako typ zmiennoprzecinkowy `float`.

Należy stosować:

```text
NUMERIC / DECIMAL
```

Przykład PostgreSQL:

```text
NUMERIC(18, 2)
```

Dla parametrów oprocentowania można zastosować większą precyzję.

---

# 61. Główne encje domenowe

Model domenowy powinien obejmować przynajmniej:

```text
User
Household
HouseholdUser
HouseholdMember

IncomeSource
MonthlyIncome

BudgetYear
BudgetMonth
BudgetGroup
BudgetCategory
BudgetItem
BudgetAllocation

Loan
LoanBorrower
LoanSchedule
LoanInstallment
LoanPayment
LoanOverpayment

FinancialAccount
FinancialTransaction

SavingsGoal
SavingsGoalAllocation

InvestmentAccount
FinancialInstrument
InvestmentTransaction
InvestmentPosition

TreasuryBondInvestment

Attachment
AuditLog
```

---

# 62. Główne relacje

```text
User
  │
  └── HouseholdUser
          │
          ▼
      Household
          │
          ├── HouseholdMember
          │       │
          │       └── IncomeSource
          │
          ├── BudgetYear
          │       └── BudgetMonth
          │
          ├── Loan
          │
          ├── FinancialAccount
          │
          └── InvestmentAccount
```

---

# 63. Wymagania niefunkcjonalne

## Wydajność

Standardowe widoki powinny odpowiadać bez zauważalnego opóźnienia dla typowego gospodarstwa domowego.

Cel:

```text
P95 < 500 ms
```

dla podstawowych operacji API bez zewnętrznych integracji.

---

## Integralność danych

Operacje obejmujące kilka zmian finansowych powinny być wykonywane transakcyjnie.

Przykład:

nadpłata kredytu + przeliczenie harmonogramu.

---

## Backup

Baza danych musi umożliwiać regularne wykonywanie kopii zapasowych.

---

## Migracje

Każda zmiana schematu bazy danych musi być wykonywana przez migracje.

Preferowane:

```text
Django migrations
```

---

# 64. MVP

Pierwsza wersja powinna koncentrować się na najważniejszych procesach.

## MVP 1 — Fundament

* logowanie,
* gospodarstwa,
* członkowie rodziny,
* źródła dochodu,
* role.

## MVP 2 — Budżet

* rok,
* miesiące,
* przychody,
* grupy,
* kategorie,
* elementy,
* rozdysponowanie środków,
* kopiowanie miesiąca,
* historia pozycji.

## MVP 3 — Kredyty

* kredyty,
* harmonogram,
* raty,
* płatności,
* nadpłaty,
* dokumenty.

## MVP 4 — Oszczędności

* rachunki,
* wpłaty,
* wypłaty,
* korekty,
* cele oszczędnościowe.

## MVP 5 — Analityka

* dashboard gospodarstwa,
* podstawowe KPI,
* analiza budżetu,
* analiza kredytów,
* analiza oszczędności.

---

# 65. Funkcjonalności po MVP

## V2

* inwestycje,
* ETF,
* akcje,
* obligacje,
* wycena aktywów.

## V3

* rzeczywiste wydatki,
* kategorie transakcji,
* plan vs wykonanie.

## V4

* synchronizacja bankowa,
* import historii rachunków,
* automatyczna klasyfikacja transakcji.

## V5

* prognozowanie finansów,
* przewidywanie salda,
* prognoza kosztów,
* symulacje kredytów,
* symulacje oszczędzania.

---

# 66. Funkcjonalności celowo poza pierwszym zakresem

W pierwszej wersji nie będą wymagane:

* automatyczne połączenie z bankiem,
* PSD2/Open Banking,
* automatyczne pobieranie transakcji,
* automatyczne rozpoznawanie wydatków,
* składanie zleceń giełdowych,
* wykonywanie przelewów,
* pełna księgowość,
* system podatkowy.

Aplikacja będzie systemem:

> **ewidencji, planowania, kontroli i analizy finansów**

a nie systemem realizującym operacje bankowe.

---

# 67. Najważniejsze reguły biznesowe

### BR-01

Użytkownik może należeć do wielu gospodarstw.

### BR-02

Członek gospodarstwa nie musi posiadać konta użytkownika.

### BR-03

Każdy obiekt finansowy należy do dokładnie jednego gospodarstwa.

### BR-04

Budżet reprezentuje plan rozdysponowania środków, a nie saldo rachunku.

### BR-05

Wartość rozdysponowanych środków może przekroczyć przychody wyłącznie po wyraźnym ostrzeżeniu.

### BR-06

Usunięcie pozycji z miesiąca nie powinno niszczyć historii poprzednich miesięcy.

### BR-07

Zmiana salda konta musi pozostawiać ślad w historii transakcji.

### BR-08

Nadpłata kredytu nie może nadpisywać poprzedniego harmonogramu bez zachowania jego wersji.

### BR-09

Zamknięcie kredytu lub konta nie usuwa jego historii.

### BR-10

Kwoty finansowe muszą być przechowywane jako wartości dziesiętne.

---

# 68. Docelowa wizja produktu

Aplikacja powinna docelowo odpowiadać na pytania:

> Ile pieniędzy miesięcznie otrzymuje nasze gospodarstwo?

> Na co planujemy przeznaczyć pieniądze?

> Ile pieniędzy pozostaje nierozdysponowanych?

> Ile mamy oszczędności?

> Na jakie cele oszczędzamy?

> Ile pozostało nam kredytów do spłaty?

> Jakie raty będziemy płacić w kolejnych miesiącach?

> Jak wpłynęłaby nadpłata kredytu na termin jego zakończenia?

> Jak szybko realizujemy cele oszczędnościowe?

> Jaka jest całkowita wartość naszego majątku netto?

> Jak zmienia się nasza sytuacja finansowa w czasie?

Ostatecznie system ma stać się prywatnym:

**Household Financial Operating System**, łączącym planowanie budżetu, zobowiązania, oszczędności, inwestycje i analitykę w jednym spójnym modelu danych.
