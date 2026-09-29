---
unit: 001-family-income-api
bolt: 010-family-income-api
stage: model
status: approved
updated: 2026-09-23T21:17:26Z
---

# Model domeny: firmy, umowy i źródła dochodu

## Granica kontekstu

Kontekst **źródeł dochodu gospodarstwa** opisuje konfigurację potencjalnych źródeł, a nie otrzymane przychody. `IncomeSource` pozostaje wspólną tożsamością źródła i przyszłym punktem wyboru na karcie miesiąca. `Contract` dodaje szczegóły tylko dla źródła rodzaju `contract`; `Company` jest słownikiem jednego gospodarstwa. Istniejący kontekst członków dostarcza aktywnego `HouseholdMember`, a kontekst dostępu dostarcza aktualną rolę użytkownika. Przychód miesięczny oraz obliczenia netto pozostają poza tym boltem.

## Encje

- **`Company`**: niezależny identyfikator, gospodarstwo, wymagana nazwa, stan aktywny/archiwalny i metadane zmiany. Firmę można użyć w wielu umowach tego samego gospodarstwa. Archiwizacja nie usuwa jej ani dotychczasowych powiązań; nowe powiązania wymagają aktywnej firmy. Nie narzucamy unikalności nazwy, której wymagania nie określają.
- **`IncomeSource`**: trwały UUID, gospodarstwo, opcjonalny członek, rozpoznawalna nazwa, rodzaj `other`/`contract`, daty, waluta, stan aktywny/archiwalny oraz pola właściwe dla źródła `other`: kategoria, płatnik, częstotliwość, regularność, opis i opcjonalna domyślna podpowiedź miesięczna. Źródło `other` może należeć do aktywnego członka albo całego gospodarstwa; nowa umowa zawsze należy do aktywnego członka. Data końca nie poprzedza początku. Źródło `contract` nie używa pól właściwych dla `other` do przechowywania warunków umowy.
- **`Contract`**: szczegóły przypisane dokładnie do jednego `IncomeSource` rodzaju `contract`: firma, typ `employment`/`mandate`/`specific_work`/`other`, opcjonalne stanowisko, własna nazwa typu `other`, nieujemna kwota brutto o dwóch miejscach dziesiętnych oraz podstawa `monthly`/`hourly`/`total`. Typ `other` wymaga własnej nazwy; stanowisko dopuszczamy dla `employment` i `mandate`. Właściciel, nazwa źródła, daty, waluta i status pochodzą ze źródła, bez ich duplikowania w umowie.
- **`HouseholdMember`**: istniejąca encja dostarczana przez kontekst członków; może istnieć bez konta i mieć wiele źródeł. Jej archiwizacja zachowuje stare źródła i umowy, ale blokuje nowe powiązania.
- **`AuditLog`**: istniejący, niezmienialny zapis udanej zmiany firmy, źródła, umowy lub jawnej konwersji. Zawiera gospodarstwo, wykonawcę, czas, akcję, typ i identyfikator obiektu oraz zredagowane stany przed/po. Powstaje w tej samej transakcji co zmiana domenowa.

## Obiekty wartości

- **`GrossAmount`**: nieujemna, skończona liczba dziesiętna z dokładnością do dwóch miejsc oraz podstawa `monthly`/`hourly`/`total`. Waluta znajduje się we wspólnym źródle. Kwota nie oznacza wartości netto ani przychodu miesiąca.
- **`MonthlyHint`**: opcjonalna kwota dziesiętna źródła `other`, z zachowaniem dwóch miejsc. Jest podpowiedzią do późniejszego formularza, nie zaksięgowanym wpływem. Migracja zachowuje istniejącą wartość.
- **`DateRange`**: data początku i opcjonalna data końca; koniec nie może być wcześniejszy od początku.
- **`SourceOwner`**: identyfikator gospodarstwa i opcjonalny identyfikator członka. Dla umowy członek jest obowiązkowy. Powiązany członek należy do tego samego gospodarstwa.
- **`OtherSchedule`**: częstotliwość i regularność tylko źródła `other`; częstotliwość jednorazowa wyklucza oznaczenie jako regularna.
- **`AuditSnapshot`**: jawna lista bezpiecznych pól stanu przed/po; nie obejmuje sekretów, sesji ani tokenów.

## Agregaty i niezmienniki

- **`Company` jako korzeń**: firma należy do dokładnie jednego gospodarstwa. Edycja lub archiwizacja nie przepisuje ani nie usuwa umów. Nowe umowy nie mogą wskazać firmy archiwalnej. Zmiana firmy i jej wpis audytu są atomowe.
- **`IncomeSource` jako korzeń ze szczegółami `Contract`**: źródło `contract` ma dokładnie jeden komplet szczegółów umowy, a `other` nie ma ich wcale. Zapis, archiwizacja i jawna konwersja zmieniają źródło, szczegóły i audyt atomowo; żaden odczyt API nie ujawnia pośredniego stanu. UUID źródła nie zmienia się przy konwersji. Wiele umów jednego członka, także z jedną firmą, jest poprawne.
- **Granica gospodarstwa**: firma, źródło, członek i umowa wskazują jedno gospodarstwo. Przy zapisie obowiązuje aktualna rola: Owner i Administrator zmieniają, Member i Viewer czytają. Reguła ADR-002 nakazuje blokadę gospodarstwa i ponowną kontrolę roli pod blokadą. Bezpośredni identyfikator obcego obiektu nie daje odczytu ani zapisu.
- **Granica historii**: archiwizacja jest logiczna; stare powiązania pozostają czytelne w historii. Brak publicznego trwałego usuwania. Zgodnie z ADR-004 udana zmiana i zredagowany audyt powstają w jednej transakcji.
- **Granica miesiąca**: żadna operacja w tym agregacie nie tworzy przychodu miesięcznego. Brutto umowy nie trafia do `default_monthly_amount`; istniejąca podpowiedź `other` nie jest traktowana jako otrzymany przychód.

## Zdarzenia domenowe

Zdarzenia oznaczają fakty do utrwalenia w istniejącym audycie. Model nie zakłada nowej kolejki ani osobnego magazynu zdarzeń.

- **`CompanyCreated` / `CompanyChanged` / `CompanyArchived`**: identyfikatory gospodarstwa, firmy i wykonawcy oraz bezpieczny stan przed/po.
- **`ContractSourceCreated` / `ContractSourceChanged` / `ContractSourceArchived`**: identyfikatory gospodarstwa, źródła, członka, firmy i wykonawcy oraz bezpieczne stany źródła i szczegółów.
- **`OtherSourceCreated` / `OtherSourceChanged` / `OtherSourceArchived`**: identyfikatory gospodarstwa, źródła i wykonawcy oraz bezpieczny stan przed/po.
- **`OtherSourceConvertedToContract`**: identyfikatory gospodarstwa, zachowanego źródła, członka, firmy i wykonawcy; stan `other` przed oraz `contract` po zmianie.

## Usługi domenowe

- **`CompanyService`**: tworzy, aktualizuje i archiwizuje firmę; sprawdza zakres gospodarstwa, rolę i stan firmy; zapisuje audyt transakcyjnie.
- **`IncomeSourceService`**: tworzy i zmienia źródła `other`, weryfikuje właściciela, daty, harmonogram i opcjonalną kwotę; archiwizuje bez usuwania historii.
- **`ContractService`**: tworzy, zmienia i archiwizuje źródło umowy ze szczegółami; sprawdza aktywnego członka i firmę tego samego gospodarstwa, typ, stanowisko, kwotę i daty.
- **`LegacySourceConversionService`**: pod blokadą źródła jawnie przekształca aktywne `other` w `contract` po dostarczeniu pełnych danych; zachowuje UUID, utrwala stan sprzed konwersji w audycie i wycofuje całość przy błędzie walidacji lub równoczesnej zmianie. Sama migracja schematu nie wywołuje tej usługi.
- **`HouseholdAccessPolicy` i `AuditWriter`**: istniejące wspólne usługi do aktualnej kontroli roli i niezmienialnego, zredagowanego audytu; nie definiujemy ich ponownie.

## Kontrakty repozytoriów

- **`CompanyRepository`**: `list_for_household`, `get_for_household`, `get_active_for_update`, `save`. Odczyt po identyfikatorze zawsze ogranicza się do gospodarstwa.
- **`IncomeSourceRepository`**: `list_for_household`, `get_for_household`, `get_for_update`, `save`. Odczyt do konwersji blokuje konkretny rekord i sprawdza bieżący rodzaj.
- **`ContractRepository`**: `get_for_source`, `save`, `list_for_household`; szczegóły są dostępne tylko przez źródło w tym samym gospodarstwie.
- **`HouseholdMemberRepository`**: `get_active_for_household`; korzysta z istniejącego kontekstu członków.
- **`AuditLogRepository`**: `append` bez możliwości zmiany lub usunięcia istniejącego wpisu; wspólny pisarz audytu kontroluje listę pól.

## Migracja istniejących danych

Każde istniejące źródło otrzymuje rodzaj `other` bez analizy nazwy, kategorii lub kwoty. Migracja zachowuje UUID, gospodarstwo, członka, pola kwotowe, walutę, daty, status i wszystkie wpisy audytu. Nie tworzy firm, umów ani przychodów miesięcznych. Dawne źródła, także należące do archiwalnych członków, pozostają czytelne; reguła aktywnego członka dotyczy nowych powiązań i jawnej konwersji. Stary endpoint może nadal odczytać dotychczasowe źródła podczas przejścia do nowego interfejsu.

## Słownik pojęć

- **Firma**: wpis słownika jednego gospodarstwa, wykorzystywany przez wiele umów.
- **Członek**: osoba w gospodarstwie, niezależna od konta użytkownika i roli aplikacyjnej.
- **Źródło dochodu**: trwała konfiguracja potencjalnego dochodu o stabilnym identyfikatorze; nie oznacza otrzymanej wpłaty.
- **Umowa**: źródło rodzaju `contract` ze szczegółami warunków i firmą, przypisane członkowi.
- **Inne źródło**: źródło rodzaju `other`, przypisane członkowi albo gospodarstwu, bez szczegółów umowy.
- **Brutto umowy**: kwota warunków umowy wraz z podstawą; nie jest automatycznym wpływem miesięcznym.
- **Podpowiedź miesięczna**: opcjonalna kwota konfiguracji innego źródła; nie jest przychodem miesiąca.
- **Konwersja**: jawna, atomowa zmiana istniejącego `other` w `contract` z zachowaniem identyfikatora i śladu audytowego.
- **Archiwizacja**: logiczne wyłączenie z nowych powiązań przy zachowaniu historii.

## Pokrycie historii

- **001-company-dictionary**: encja i agregat `Company`, zakres gospodarstwa, archiwizacja i role.
- **002-contract-sources**: `IncomeSource` + `Contract`, aktywny członek i firma, kwota brutto, daty, audyt i brak zapisu przychodu miesięcznego.
- **003-other-sources**: `other`, opcjonalny właściciel, harmonogram, opcjonalna podpowiedź i zgodny odczyt.
- **004-legacy-source-migration**: zachowanie dawnych rekordów jako `other`, stabilny UUID, jawna konwersja i atomowe wycofanie błędu.

## Decyzje do projektu technicznego

Szczegółowe pola bazy, ścieżki i kształt odpowiedzi API, wykrywanie równoczesnej zmiany oraz kolejność blokad powstaną w etapie projektu technicznego. Model przyjmuje istniejące ADR-002 i ADR-004 jako obowiązujące ograniczenia.
