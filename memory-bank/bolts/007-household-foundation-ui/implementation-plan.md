---
stage: plan
bolt: 007-household-foundation-ui
status: accepted
created: 2026-09-21T19:28:14Z
---

# Plan implementacji: członkowie, relacje i źródła dochodu

## Cel i zakres

Rozszerzyć działający interfejs gospodarstwa o stories 004–005: zarządzanie osobami należącymi do gospodarstwa, konfigurowalnymi relacjami oraz źródłami dochodu. Frontend korzysta z ukończonego API bolta 005 i nie powiela jego reguł autoryzacji, izolacji gospodarstw, walidacji powiązań ani archiwizacji.

Zakres obejmuje FR-06–FR-08. Poza zakresem pozostają transakcje, budżety miesięczne, prognozy, kredyty, inwestycje, importy oraz panel analityczny. Kwota domyślna źródła dochodu jest wyłącznie parametrem planowania i nie tworzy operacji finansowej.

## Rezultaty

1. Nawigacja w aktywnym gospodarstwie pomiędzy dostępami, członkami i dochodami, z zachowaniem bieżącego wyboru gospodarstwa i roli.
2. Lista członków z nazwą, opcjonalnym kontem, relacją i stanem aktywności; formularze dodawania oraz edycji; dezaktywacja po potwierdzeniu.
3. Lista konfigurowalnych relacji rodzinnych z dodawaniem, zmianą nazwy i dezaktywacją dla Ownera i Administratora.
4. Lista źródeł dochodu z kompletem pól FR-08, dodawaniem, edycją i dezaktywacją oraz jednoznacznym przypisaniem do gospodarstwa albo aktywnego członka.
5. Tryb odczytu dla Membera i Viewera, bez aktywnych kontrolek zapisu; każda mutacja nadal podlega weryfikacji API.
6. Paginacja, puste stany, stany ładowania i błędów, komunikaty sukcesu oraz odporność na spóźnione odpowiedzi po zmianie gospodarstwa lub sekcji.
7. Testy izolowane UI, test pełnego przepływu przez HTTPS/API/PostgreSQL, kontrola jakości i raporty etapów.

## Kontrakty API i zależności

- Użyć istniejących zasobów `/api/households/{id}/members/`, `relation-types/` i `income-sources/`; tworzenie przez POST, edycja przez PATCH, dezaktywacja przez POST do `/{record_id}/deactivate/`.
- Listy rekordów są stronicowane do 50 pozycji i zwracają `count`, `next`, `previous`, `results`. Frontend utrzymuje numer strony osobno dla każdej listy i buduje względny parametr `?page=`, zamiast przekazywać klientowi API pełne adresy z odpowiedzi.
- Lista `memberships/` dostarcza kont dostępnych do powiązania z członkiem. Opcja „Bez konta” wysyła `account_id: null`. Powiązanie jest możliwe tylko z aktywnym kontem mającym dostęp do tego samego gospodarstwa; ostatecznie rozstrzyga to serwer.
- Relacja jest opcjonalna i musi pochodzić z tego samego gospodarstwa. Formularz członka korzysta z aktywnych relacji, a archiwalne rekordy zachowują historyczne identyfikatory.
- Źródło dochodu może należeć bezpośrednio do gospodarstwa (`member_id: null`) albo do aktywnego członka. Endpoint przyjmuje: `name`, `category`, `payer`, `start_date`, `end_date`, `default_monthly_amount`, `currency`, `frequency`, `is_regular`, `description` i opcjonalny `member_id`.
- Obsługiwane częstotliwości: miesięcznie, tygodniowo, kwartalnie, rocznie, jednorazowo i nieregularnie. Waluta ma trzy wielkie litery, kwota maksymalnie 18 cyfr z dwoma miejscami po przecinku, a data końcowa nie może poprzedzać początkowej.
- Owner i Administrator mają capability zapisu danych. Member i Viewer mogą odczytywać. Widoczność kontrolek wynika z aktualnej roli, lecz nie zastępuje odpowiedzi 403 z API.
- Dezaktywowane rekordy pozostają na liście jako archiwalne, nie są edytowalne i zachowują powiązania historyczne. Zmiany źródeł dochodu są audytowane atomowo przez backend.

## Architektura interfejsu

- Rozszerzyć `HouseholdShell` o wewnętrzną sekcję aktywnego gospodarstwa: „Dostępy”, „Członkowie” i „Dochody”. Zmiana gospodarstwa przywraca bezpieczny widok startowy, czyści komunikaty i unieważnia odczyty starego kontekstu.
- Zachować `AccessPanel` jako odpowiedzialny wyłącznie za role i zaproszenia. Dodać oddzielne panele dla członków/relacji i dochodów, bez łączenia formularzy domenowych z logiką powłoki aplikacji.
- Wspólne typy rekordów, odpowiedź stronicowana, mapy częstotliwości oraz funkcje budowania ścieżek umieścić przy istniejącym kliencie API. Współdzielić komponenty formularzy, komunikatów i potwierdzeń zamiast kopiować ich obsługę.
- Każdy panel pobiera dane dla własnego gospodarstwa z `AbortController` oraz wersją kontekstu. Mutacja pokazuje sukces dopiero po odpowiedzi serwera i ponownym odczycie odpowiedniej listy. Odpowiedź zakończona po zmianie sekcji lub gospodarstwa nie może zmienić nowego widoku.
- Członkowie i relacje mogą być pokazani w jednym obszarze zadaniowym: główna lista osób oraz osobny, jasno nazwany panel konfiguracji relacji. Formularz osoby oferuje nazwę, relację i opcjonalne konto z listy dostępów.
- Dochody otrzymują osobną listę oraz formularz wszystkich pól. Wiersz/karta pokazuje kwotę domyślną, walutę, częstotliwość, zakres dat, płatnika, przypisanie, regularność i status. Szczegóły opisu pozostają czytelne bez przeciążenia listy.
- Na szerokim ekranie użyć istniejącego układu tabel/paneli, a na małym ekranie zachować przewijanie i logiczną kolejność pól. Nawigacja, formularze, potwierdzenia i paginacja muszą działać klawiaturą oraz mieć widoczny focus.

## Dane, precyzja i walidacja

- Kwoty przechowywać w stanie formularza i przesyłać jako tekst dziesiętny. Do wyświetlania użyć formattera działającego na częściach tekstu, bez konwersji całej wartości na `number`, aby nie tracić precyzji wartości `Decimal(18,2)`.
- Pole kwoty akceptuje nieujemną wartość z najwyżej dwoma miejscami po separatorze; przed wysłaniem separator przecinkowy jest normalizowany do kropki. Odpowiedź serwera pozostaje źródłem prawdy dla granic i walidacji.
- Walutę źródła domyślnie wypełnić walutą gospodarstwa, ale pozostawić edytowalną jako trzyliterowy kod zgodny z FR-08.
- Edycja wysyła jawnie wartości opcjonalne, w tym `null` dla usuniętego członka, relacji lub daty końcowej oraz pusty tekst dla płatnika i opisu. Pozwala to usunąć wcześniejszą wartość, a nie tylko pominąć pole w PATCH.
- Błędy pól z API rozszerzyć o nazwy używane przez członków, relacje i dochody. Nie pokazywać surowej treści odpowiedzi 5xx. Po 401/403 odświeżyć sesję i aktualną rolę, bez komunikowania pozornego sukcesu.
- Dezaktywacja wymaga jawnego potwierdzenia z nazwą rekordu. Anulowanie nie wykonuje żądania i przywraca focus. Po sukcesie lista pokazuje stan „Archiwalne”.

## Plan implementacji

1. Rozszerzyć typy klienta API, bezpieczne mapowanie błędów oraz współdzielone funkcje paginacji i formatowania kwot.
2. Dodać nawigację sekcji gospodarstwa i reset kontekstu w `HouseholdShell`, zachowując dotychczasowy przepływ tworzenia gospodarstwa.
3. Zbudować panel członków i relacji: pobieranie list, paginację, widok odczytu, formularze dodawania/edycji oraz potwierdzoną dezaktywację.
4. Zbudować panel dochodów z pełnym formularzem FR-08, formatowaniem kwot, listą i operacjami zapisu zależnymi od roli.
5. Uzupełnić responsywne style i dostępność stanów interakcji zgodnie z istniejącym design-system.md.
6. Po każdym zmienionym pliku uruchomić Prettier, a dla TypeScript/TSX także ESLint; dla CSS także Stylelint. Sprawdzić odpowiedzialności i brak duplikacji przed przejściem dalej.
7. Sporządzić walkthrough implementacji i zatrzymać się na checkpoint przed etapem testów.

## Plan weryfikacji

- Testy izolowane sprawdzą puste i zapełnione listy, paginację, ponowienie po błędzie, zmianę gospodarstwa w trakcie odczytu i zapisu oraz brak nadpisania nowego kontekstu przez starą odpowiedź.
- Dla członków sprawdzić utworzenie osoby bez konta, dodanie relacji, edycję, powiązanie aktywnego konta, usunięcie powiązania, odrzucenie konta spoza gospodarstwa, archiwizację i prezentację rekordu historycznego.
- Dla relacji sprawdzić tworzenie, zmianę nazwy, konflikt aktywnej nazwy, dezaktywację i możliwość późniejszego ponownego użycia nazwy zgodnie z API.
- Dla dochodów sprawdzić wszystkie częstotliwości, źródło gospodarstwa i członka, opcjonalne pola, walutę, precyzyjną kwotę, błędny zakres dat, edycję, archiwizację i wyjaśnienie znaczenia kwoty domyślnej.
- Dla ról sprawdzić zapis Ownera i Administratora, brak aktywnych kontrolek dla Membera i Viewera oraz odmowę API po odebraniu uprawnienia w innej sesji.
- Pełny test przez działające HTTPS/API/PostgreSQL utworzy odizolowane dane: gospodarstwo, dostęp, relację, członka i źródło dochodu; zweryfikuje tryb odczytu drugiego konta, archiwizację oraz posprząta wszystkie dane testowe.
- Uruchomić `scripts/quality.ps1`, pełny zestaw testów Django, izolowane testy Playwright, pełny scenariusz Playwright i kontrole runtime adekwatne do zmiany. Raport rozdzieli wyniki kontrolowanego UI i rzeczywistego stosu.

## Kryteria zakończenia

- [ ] Wszystkie kryteria stories 004–005 są dostępne w interfejsie i potwierdzone testami.
- [ ] Owner/Administrator mogą zarządzać danymi, a Member/Viewer otrzymują spójny tryb odczytu z serwerową ochroną zapisu.
- [ ] Paginacja, puste stany, błędy, potwierdzenia i zmiana kontekstu działają bez ujawniania danych innego gospodarstwa.
- [ ] Kwoty `Decimal(18,2)` są wysyłane i wyświetlane bez utraty precyzji, razem z walutą.
- [ ] Rekordy dezaktywowane pozostają widoczne jako archiwalne i nie tracą historycznych powiązań.
- [ ] Formatowanie, lint, testy aplikacji i rzeczywisty scenariusz integracyjny kończą się powodzeniem.

## Checkpoint

Plan zatwierdzony przez użytkownika poleceniem „continue”. Implementację rozpoczęto 2026-09-21T19:28:14Z.
