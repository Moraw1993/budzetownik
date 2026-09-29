---
unit: 001-family-income-api
bolt: 010-family-income-api
stage: design
status: approved
updated: 2026-09-23T21:21:31Z
---

# Projekt techniczny: API firm, umów i źródeł dochodu

## Wzorzec architektoniczny

Rozszerzamy istniejący modularny monolit Django i aplikację `households`. Obecny podział na modele, selektory, transakcyjne usługi, serializatory i cienkie widoki DRF pozostaje obowiązujący. Wspólne zasady dostępu i audytu pochodzą z ADR-002 i ADR-004. Nie dodajemy usługi zewnętrznej, drugiego systemu autoryzacji ani osobnego magazynu zdarzeń.

`IncomeSource` jest korzeniem agregatu źródła. `Contract` stanowi szczegóły 1:1, a `Company` jest odrębną encją słownika gospodarstwa. Przypadki użycia usługowe są jedyną publiczną drogą zapisu tych obiektów. Szczegóły umowy i wpis audytu powstają w jednej transakcji ze źródłem.

## Odpowiedzialności warstw

1. **Widoki HTTP**: sesja, CSRF, mapowanie ścieżek i kodów odpowiedzi, bez reguł domenowych.
2. **Serializatory**: ścisły kontrakt wejścia i wyjścia, typy pól, precyzja kwot, odrzucenie nieznanych pól; wynik walidacji domenowej nadal należy do usług.
3. **Usługi przypadków użycia**: blokada gospodarstwa, ponowna kontrola roli, sprawdzenie powiązań, transakcje, zmiana wersji źródła i zredagowany audyt.
4. **Selektory**: odczyty wyłącznie w zakresie gospodarstwa, paginacja i pobranie szczegółów umowy z firmą oraz członkiem.
5. **Modele i migracje**: trwałość, klucze, indeksy i ograniczenia lokalne dla wiersza. Niezmiennik `contract` ma szczegóły 1:1 jest egzekwowany przez atomowy zapis usługi, bo obejmuje dwie tabele.

Przed implementacją należy wyszukać istniejące funkcje dostępu, selektory, serializatory i pisarza audytu i je rozszerzyć; projekt nie nakazuje powielania tych funkcji pod nowymi nazwami.

## Kontrakty API

Wszystkie poniższe ścieżki mają prefiks `/api/households/{household_id}/`, wymagają sesji i podlegają aktualnemu członkostwu. Każdy zapis wymaga CSRF. Listy zachowują istniejącą paginację `{count, next, previous, results}` z 50 rekordami na stronę i parametrem `page`. Identyfikator gospodarstwa pochodzi wyłącznie z URL. Klient nie ustawia identyfikatora obiektu, wykonawcy, audytu, `is_active` ani `kind` wbrew wybranemu endpointowi.

### Firmy

- **`GET companies/`**: lista `{id, name, is_active, archived_at}` w gospodarstwie; opcjonalny filtr `is_active=true|false`. Wszystkie cztery role czytają.
- **`POST companies/`**: `{name}`; `201` z firmą. Nazwa po usunięciu białych znaków nie może być pusta, maksimum 180 znaków. Tylko Owner i Administrator.
- **`GET companies/{company_id}/`**: szczegóły firmy w gospodarstwie; także archiwalnej.
- **`PATCH companies/{company_id}/`**: `{name}`; `200` z firmą. Edycja archiwalnej firmy jest odrzucona; zmiana nazwy nie zmienia identyfikatora ani dotychczasowych umów.
- **`POST companies/{company_id}/archive/`**: puste ciało; `200` z archiwalną firmą. Ponowna archiwizacja jest idempotentna, bez nowego wpisu audytu. Brak publicznego `DELETE`.

### Umowy

- **`GET contracts/`**: lista umów gospodarstwa z polami źródła `{id, kind: "contract", member_id, name, start_date, end_date, currency, is_active, deactivated_at, version}` i szczegółami `{company: {id, name, is_active}, contract_type, other_type_name, position, gross_amount, gross_basis}`. `gross_amount` jest tekstem dziesiętnym. Opcjonalny filtr `member_id` działa tylko w tym gospodarstwie.
- **`POST contracts/`**: `{member_id, company_id, name, contract_type, other_type_name?, position?, gross_amount, gross_basis, currency, start_date, end_date?}`; `201` z kompletną umową. Członek i firma muszą być aktywni i należeć do gospodarstwa. `name` jest wymagane i widoczne na liście źródeł. Typ `other` wymaga `other_type_name`; inne typy tego pola nie przyjmują. `position` jest dopuszczalne tylko dla `employment` i `mandate`. Brutto jest nieujemną liczbą z najwyżej dwoma miejscami po przecinku, o zakresie zgodnym z `Decimal(18,2)`. Waluta to trzy wielkie litery.
- **`GET contracts/{source_id}/`**: szczegóły przez UUID `IncomeSource`, także po archiwizacji firmy lub członka. Obcy identyfikator jest nierozróżnialny od nieistniejącego.
- **`PATCH contracts/{source_id}/`**: wybrane pola utworzenia oraz opcjonalne `expected_version`; `200` z nową wersją. Zmiana członka lub firmy wymaga aktywnego obiektu w tym gospodarstwie; niezmienione powiązanie do obiektu później zarchiwizowanego wolno zachować. Edycja archiwalnej umowy jest odrzucona. `kind`, `default_monthly_amount` i pola `other` są niedozwolone.
- **`POST contracts/{source_id}/archive/`**: puste ciało; `200` z archiwalną umową, idempotentnie bez dodatkowego audytu. Archiwizuje źródło, zachowuje szczegóły i firmę.

### Inne źródła i zgodność starego API

- **`GET income-sources/` oraz `GET income-sources/{source_id}/`**: nadal obsługują istniejące rekordy i identyfikatory. Odpowiedź zachowuje dotychczasowe pola, dodając `kind`, `version` i jednoznaczny `member_id` (`null` oznacza gospodarstwo). Dla `contract` dostępne są pola wspólne; szczegóły pochodzą z `contracts/{source_id}/`. Lista obejmuje `other` i `contract`, w tym archiwalne, rozróżnione przez `is_active`.
- **`POST income-sources/`**: tworzy tylko `other`. Brak `kind` w dawnym żądaniu oznacza `other`; jawne `kind: "other"` jest akceptowane, `contract` odrzucone ze wskazaniem endpointu umów. Wymaga `name`, `category`, `currency`, `start_date`, `frequency`, `is_regular`; zachowuje istniejące opcjonalne `member_id`, `payer`, `end_date`, `description` i dopuszcza puste `default_monthly_amount`. Jednorazowa częstotliwość wyklucza regularność. Nowe powiązanie członka wymaga aktywnego członka.
- **`PATCH income-sources/{source_id}/`**: edytuje wyłącznie `other` i zachowuje stare nazwy pól; `kind` i szczegóły umowy są niemodyfikowalne tą drogą. Zwraca `200` z nową wersją. Dla `contract` zwraca konflikt z instrukcją użycia endpointu umowy.
- **`POST income-sources/{source_id}/deactivate/`**: dotychczasowa ścieżka działa dla `other`; dla `contract` należy użyć `contracts/{source_id}/archive/`. Operacja jest idempotentna i audytuje tylko rzeczywistą zmianę.
- **`POST income-sources/{source_id}/convert-to-contract/`**: `{expected_version, member_id, company_id, name, contract_type, other_type_name?, position?, gross_amount, gross_basis, currency, start_date, end_date?}`; `200` w formacie szczegółów umowy. Wymaga aktywnego `other`, aktywnego członka i firmy z tego samego gospodarstwa oraz pełnych danych umowy. Po sukcesie zachowuje UUID źródła, zmienia `kind`, zapisuje `Contract`, usuwa bieżące pola właściwe wyłącznie dla `other` i zwiększa `version`. Stan przed, w tym dawną kwotę, zapisuje w audycie. Nie tworzy przychodu miesięcznego. Puste lub nieaktualne `expected_version` odpowiednio odrzuca.

Odpowiedzi źródeł `other` zachowują dotychczasową kwotę jako tekst dziesiętny lub `null`; klient prezentuje ją jako opcjonalną podpowiedź. Brutto umowy jest widoczne wyłącznie pod jednoznaczną nazwą `gross_amount` razem z `gross_basis`. Żadna odpowiedź nie określa tych wartości mianem przychodu miesiąca.

## Model trwałości i migracja

- **`Company`**: UUID, `household_id` z `PROTECT`, `name` do 180 znaków, `is_active`, odziedziczone `deactivated_at` i znaczniki czasu. API prezentuje ten znacznik jako `archived_at`. Indeks po `(household_id, is_active, name)`. Brak ograniczenia unikalności nazwy.
- **`IncomeSource`**: istniejący UUID, gospodarstwo i opcjonalny członek bez zmiany. Dodać `kind` (`other`/`contract`, indeks po gospodarstwie i rodzaju) oraz dodatni `version` zaczynający się od 1. `default_monthly_amount` staje się opcjonalną wartością `Decimal(18,2)`; istniejące niepuste kwoty nie zmieniają się. Pola właściwe dla `other` mogą być puste dla `contract`; API waliduje kompletność `other` przy nowym zapisie. `name`, waluta, daty i status pozostają wspólne. Ograniczenia bazy: dopuszczalny `kind`, dodatnia wersja, data końca nieprzed datą początku, nieujemna podana podpowiedź.
- **`Contract`**: UUID techniczny lub PK 1:1 do `IncomeSource` z `PROTECT`, `company_id` z `PROTECT`, `contract_type`, opcjonalne `other_type_name` i `position`, `gross_amount Decimal(18,2)`, `gross_basis`, znaczniki czasu. Unikalność źródła zapewnia `OneToOne`. Ograniczenia bazy: nieujemne brutto, dopuszczalny typ i podstawa, wymagana własna nazwa dla typu `other`. Zgodność gospodarstwa, aktywność powiązań i istnienie szczegółów dla `kind=contract` sprawdza usługa w transakcji.
- **`AuditLog`**: istniejące identyfikatory, dane i sposób odczytu pozostają bez migracji destrukcyjnej. Nowe akcje firm, umów i konwersji używają istniejącego pisarza z whitelistą pól. Snapshot konwersji obejmuje całe bezpieczne znaczenie starego źródła, zwłaszcza kwotę, kategorię i częstotliwość.

Migracja Django dodaje nowe tabele i pola, ustawia `kind=other` oraz `version=1` dla wszystkich wcześniejszych źródeł i dopiero potem wzmacnia ograniczenia. Nie klasyfikuje po nazwie ani kategorii, nie tworzy `Contract` i nie dotyka przyszłych przychodów miesięcznych. Test migracyjny uruchomi stary schemat, zapisze syntetyczne źródła i audyt, zastosuje nową migrację, po czym porówna liczbę i identyfikatory rekordów, właścicieli, kwoty, daty, waluty, statusy i wpisy audytu. Sprawdzi też `kind=other`, brak kontraktów i poprawny odczyt przez stary endpoint.

## Transakcje i współbieżność

Każdy zapis działa w `transaction.atomic()`. Najpierw blokuje `Household`, ponownie sprawdza członkostwo i rolę, następnie pobiera źródło do zapisu pod blokadą oraz powiązane obiekty w tym gospodarstwie. Wszystkie publiczne zapisy do tego gospodarstwa używają tej samej kolejności. Tworzenie lub aktualizacja źródła oraz wpis audytu kończą się razem albo nie zachodzi żadna zmiana.

Konwersja wymaga `expected_version` z ostatniego odczytu klienta. Porównanie następuje pod blokadą źródła; niezgodność zwraca `409` bez zmiany i audytu. Każda udana edycja źródła zwiększa wersję, w tym edycja przez dawny endpoint. Dwukrotna konwersja tego samego źródła zwraca konflikt. Blokada gospodarstwa serializuje też archiwizację firmy lub członka z utworzeniem nowego powiązania. Testy współbieżności muszą użyć PostgreSQL, nie zachowania SQLite.

## Bezpieczeństwo i błędy

- **Sesja i CSRF**: istniejący mechanizm Django/DRF według ADR-001. Brak sesji nie daje odczytu; zapisy bez CSRF są odrzucane.
- **Role**: wszystkie role odczytują w swoich gospodarstwach; Owner i Administrator zapisują. Odwołanie członkostwa lub zmiana roli działa od razu, również w już istniejącej sesji.
- **Izolacja**: selektory po `(household_id, object_id)`; brak gospodarstwa, członkostwa lub obcy identyfikator daje jednakowe `404`. Niewystarczająca rola w dostępnym gospodarstwie daje `403`.
- **Walidacja**: niepełne lub błędne dane, obcy lub archiwalny nowy członek/firma, zła data, niepoprawna kwota albo niezgodny typ dają `400` z nazwą pola, bez częściowego zapisu. Nieaktualna wersja, już skonwertowane źródło albo próba edycji rodzaju niewłaściwym endpointem dają `409`. Niedozwolony `DELETE` daje `405`.
- **Audyt**: tylko Owner czyta istniejący endpoint audytu; brak publicznego zapisu, edycji i usuwania wpisów. Whitelista snapshotów wyklucza sekrety. Nieudana albo idempotentna operacja bez zmiany nie tworzy nowego wpisu.

## Wymagania niefunkcjonalne i integracje

- **Integralność**: kwoty wyłącznie dziesiętne, transakcja dla źródła i szczegółów, ograniczenia lokalne bazy, logiczna archiwizacja. Migracja zachowuje dane starego schematu i audyt.
- **Wydajność**: listy paginowane, indeksy po gospodarstwie, rodzaju, aktywności i właścicielu, pobieranie powiązanych członków i firm bez zapytań na każdy wiersz. Pomiar P95 dla podstawowych operacji w lokalnym środowisku pozostaje bramką testową; wynik nie jest zakładany z góry.
- **Zgodność**: stare `income-sources/` czyta wszystkie stare rekordy i nadal przyjmuje dawny format tworzenia/edycji `other`. Nowe kontrakty mają osobny endpoint, więc stary klient nie musi wysyłać nieznanych pól. Dodane pola odpowiedzi są opcjonalne dla dotychczasowych ekranów.
- **Integracje**: nowe zasoby wykorzystują istniejące gospodarstwa, członków, role, audyt i lokalny PostgreSQL. Nie powstaje miesięczny przychód, płatność, rozliczenie płac ani połączenie z usługą zewnętrzną. Bolt 011 użyje opisanych kontraktów w UI.

## Zakres weryfikacji dla etapu testów

Testy obejmą macierz czterech ról, brak sesji i CSRF, obce identyfikatory, archiwalne powiązania, warianty typów i kwot, daty, jednorazowość, audyt, stabilność UUID, odczyt starego endpointu, brak miesięcznego przychodu oraz wycofanie konwersji przy błędzie i konflikcie wersji. Osobny test ze schematu sprzed migracji sprawdzi zachowanie danych. Testy PostgreSQL potwierdzą wyścig edycji z konwersją oraz archiwizacji firmy z utworzeniem umowy. Kontrola jakości obejmie Ruff, odpowiednie testy Django i `scripts/quality.ps1`.
