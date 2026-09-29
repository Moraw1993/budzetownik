---
intent: 002-family-income-management
phase: inception
status: construction
created: 2026-09-23T08:15:53Z
updated: 2026-09-23T21:12:14Z
---

# Wymagania: Zarządzanie rodziną, umowami i źródłami dochodu

## Cel

Uporządkować członków gospodarstwa, firmy, umowy oraz inne źródła dochodu. Umowa jest jednym z rodzajów źródła dochodu i zawiera dodatkowe warunki. Kwota brutto zapisana na umowie opisuje te warunki; nie jest kwotą przychodu otrzymaną w danym miesiącu. Miesięczne przychody będą realizowane później na karcie miesiąca. Rozszerzenie istniejącego fundamentu nie zmienia zakresu trwającego bolta 009.

## Zakres

- Sekcja „Zarządzanie rodziną” pokazuje członków, ich umowy i inne źródła dochodu oraz źródła przypisane całemu gospodarstwu.
- Formularze „Dodaj członka rodziny”, „Dodaj umowę” i „Dodaj inne źródło dochodu” prowadzą do odrębnych zapisów. Nazwa ostatniej akcji odróżnia konfigurację źródła od późniejszego „Dodaj przychód” na karcie miesiąca.
- Firma jest odrębnym wpisem w słowniku gospodarstwa, możliwym do ponownego użycia przy wielu umowach.
- Jedna osoba może mieć wiele umów i innych źródeł dochodu; źródło bez przypisanej osoby należy do całego gospodarstwa.
- W tym etapie nie powstają przychody miesięczne, księgowość płac ani automatyczne wyliczanie kwoty netto z umowy.

## Wymagania funkcjonalne

### FR-01: Nawigacja i członkowie rodziny

- **Opis:** W obrębie wybranego gospodarstwa dostępny jest dział „Zarządzanie rodziną” z listą członków i akcją „Dodaj członka rodziny”.
- **Kryteria:** Członek może istnieć bez konta, umowy i źródła dochodu. Po otwarciu członka widać jego umowy oraz inne źródła; źródła całego gospodarstwa mają osobne, jednoznaczne miejsce. Zmiana gospodarstwa zmienia wszystkie te listy.
- **Priorytet:** Must.

### FR-02: Słownik firm

- **Opis:** Użytkownik z uprawnieniem do edycji może utworzyć firmę w obrębie gospodarstwa i wybrać istniejącą firmę przy dodawaniu kolejnej umowy.
- **Kryteria:** W pierwszej wersji jedynym wymaganym polem firmy jest nazwa. Firma ma identyfikator niezależny od umowy; zmiana danych firmy nie zmienia danych firmy w innym gospodarstwie. Umowa zachowuje odwołanie do firmy.
- **Priorytet:** Must.

### FR-03: Umowa członka rodziny

- **Opis:** Akcja „Dodaj umowę” tworzy źródło dochodu typu umowa, przypisane do członka gospodarstwa. Formularz pozwala wybrać typ umowy (praca, zlecenie, dzieło lub inne), firmę, datę początku i opcjonalną datę końca, stanowisko gdy ma zastosowanie, kwotę brutto, podstawę tej kwoty (miesięcznie, godzinowo lub za całość) i walutę.
- **Kryteria:** Firma i członek należą do tego samego gospodarstwa co umowa. Data końca nie poprzedza początku. Stanowisko jest dostępne dla typów umów, dla których ma sens, w szczególności umowy o pracę i zlecenia. Można zapisać kilka umów jednego członka. Umowa ma rozpoznawalną nazwę na przyszłej liście źródeł. Wpisanie lub zmiana kwoty brutto nie tworzy przychodu miesięcznego.
- **Priorytet:** Must.

### FR-04: Inne źródło dochodu

- **Opis:** Akcja „Dodaj inne źródło dochodu” zapisuje źródło niezwiązane z umową, np. świadczenie, najem lub odsetki. Źródło można przypisać członkowi albo bezpośrednio całemu gospodarstwu.
- **Kryteria:** Źródło ma nazwę, kategorię, daty obowiązywania, walutę oraz pozostałe dane źródła uzgodnione w FR-08 poprzedniego intentu. Domyślna miesięczna kwota jest opcjonalną podpowiedzią. Źródło nie wymaga firmy, stanowiska ani kwoty umowy. Osoba może mieć wiele źródeł; źródło z pustym przypisaniem do osoby należy do gospodarstwa. Zapis źródła nie tworzy przychodu miesięcznego.
- **Priorytet:** Must.

### FR-05: Granica między źródłem a miesięcznym przychodem

- **Opis:** Ten etap przygotowuje źródła do przyszłego modułu miesiąca, bez zapisywania przychodów miesięcznych.
- **Kryteria:** Zapis lub zmiana umowy albo innego źródła nie tworzy miesięcznego przychodu. Przyszły formularz „Dodaj przychód” na karcie miesiąca ma wybierać osobę lub całe gospodarstwo, a następnie źródło należące do tego wyboru i rzeczywistą kwotę tego miesiąca. Kwota przychodu może różnić się od kwoty brutto umowy. Kwota umowy nie jest dodawana do sumy przychodów miesiąca.
- **Priorytet:** Must.

### FR-06: Istniejące źródła dochodu i historia

- **Opis:** Rozszerzenie obecnych źródeł dochodu o umowy i firmy nie gubi danych ani historii zmian.
- **Kryteria:** Istniejące źródło nie jest automatycznie uznawane za umowę ani za otrzymany przychód w żadnym miesiącu. Migracja oznacza je jako inne źródło i zachowuje identyfikator, powiązanie z członkiem, kwotę, daty, status i audyt. Użytkownik może jawnie uzupełnić brakujące dane firmy i umowy przy przekształceniu takiego źródła w umowę; operacja nie tworzy przychodu miesięcznego.
- **Priorytet:** Must.

### FR-07: Dostęp i izolacja

- **Opis:** Uprawnienia do odczytu i zmiany danych rodzinnych oraz finansowych są egzekwowane w API dla każdego gospodarstwa.
- **Kryteria:** Obowiązują role już uzgodnione dla członków i źródeł dochodu: Owner i Administrator edytują, Member i Viewer odczytują. Nie można powiązać źródła, umowy, firmy lub członka z innym gospodarstwem. Istotne zmiany pozostawiają ślad audytowy.
- **Priorytet:** Must.

## Wymagania niefunkcjonalne i ograniczenia

- **NFR-01 — Bezpieczna migracja:** test na danych ze starego schematu potwierdza niezmienione identyfikatory, wartości i liczbę istniejących źródeł oraz wpisów audytu; migracja nie tworzy umów ani miesięcznych przychodów.
- **NFR-02 — Jednoznaczność kwot:** wszystkie widoki i formularze nazywają kwotę umowy „brutto” wraz z podstawą, a kwotę innego źródła „opcjonalną podpowiedzią miesięczną”; żadna nie jest prezentowana jako przychód miesiąca.
- **NFR-03 — Zgodność przejściowa:** istniejące źródła pozostają czytelne przez obecny endpoint i ekran do chwili zastąpienia ekranu w bolcie UI.
- Kwoty pozostają dziesiętne; granice uprawnień i izolacja gospodarstw są sprawdzane przez backend zgodnie ze standardami projektu.

## Założenia do potwierdzenia

- „Dodaj przychód” będzie akcją przyszłej karty miesiąca, a „Dodaj inne źródło dochodu” akcją konfiguracji źródła.
- Umowa dotyczy członka rodziny; inne źródło dochodu może należeć do członka lub całego gospodarstwa.
- Firma jest słownikiem należącym do gospodarstwa, nie globalnym słownikiem wszystkich użytkowników. W pierwszej wersji wystarcza jej nazwa.
- Początkowe typy umów to praca, zlecenie, dzieło i inne.
- Przy umowie zapisuje się podstawę kwoty brutto: miesięcznie, godzinowo albo za całość.
- Domyślna miesięczna kwota innego źródła jest opcjonalną podpowiedzią.

## Otwarte decyzje

1. Plan zakłada istniejący, nieusuwalny audyt zmian umowy i firmy bez osobnego wersjonowania umów. Przyszły projekt przychodów miesięcznych musi określić, jakie dane źródła utrwala przy zapisie miesiąca.
