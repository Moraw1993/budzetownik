---
stage: design
bolt: 003-foundation-api
created: 2026-09-10T05:59:24.568Z
---
# Projekt techniczny gospodarstw

Django app households: modele, polityka uprawnień, selektory, transakcyjne usługi, serializatory i widoki API w osobnych plikach.
Wspólny PrivateAPIView w common obsługuje Cache-Control: no-store dla kont i gospodarstw.

## Dane
Household: UUID, name (180), currency (3 wielkie litery, domyślnie PLN), created_at.
Membership: UUID, household FK, user FK PROTECT, role, created_at; unikalność (household, user), ograniczenie wartości roli w bazie.
Waluta przy tworzeniu jest kodem trzyliterowym; jej zmiana nie jest udostępniona w tym etapie (bez przeliczania historycznych kwot).

## Kontrakt API
Wszystkie adresy poniżej wymagają sesji. Zapisy wymagają CSRF.
- GET /api/households/: lista {id, name, currency, role, membership_id}, tylko własne gospodarstwa.
- POST /api/households/: {name, currency?}; 201, gospodarstwo z rolą Owner.
- GET /api/households/{id}/: bieżące dane i własna rola.
- PATCH /api/households/{id}/: {name}, Owner/Administrator; 200.
- GET /api/households/{id}/memberships/: lista {id, user_id, username, role}, wszystkie role.
- PATCH /api/households/{id}/memberships/{membership_id}/: {role}, tylko Owner.
- DELETE ten sam adres: odebranie dostępu, 204, tylko Owner.
- POST /api/households/{id}/transfer-ownership/: {membership_id}; 200, własne członkostwo po przekazaniu.

Wybrane gospodarstwo to jawny identyfikator w adresie żądania; frontend będzie przechowywał wybór. Brak globalnego aktywnego gospodarstwa w sesji zapobiega mieszaniu kart przeglądarki.
Brak członkostwa i nieistniejący zasób zwracają ten sam 404; niewystarczająca rola w swoim gospodarstwie 403; ostatni Owner 409; błędne dane 400.
Nieznane pola wejściowe są odrzucane; klient nie ustawia własnej roli, identyfikatora ani wykonawcy.

## Transakcje i dostęp
Wspólne capability: read, edit_data, manage_access. Macierz z zatwierdzonych wymagań.
Wszystkie zapisy istniejącego agregatu blokują wiersz Household przez select_for_update w transaction.atomic. Po uzyskaniu blokady ponownie pobierają członkostwo wykonawcy. Kontrola ostatniego Owner odbywa się pod tą samą blokadą.
Listy filtrują po członkostwie; szczegóły zasobów zawsze po household_id i resource_id. Role nie są cacheowane w sesji. Konto superuser nie omija członkostwa.
Politykę wykorzystają też bolty 004–005; testy HTTP zaproszeń, członków i dochodów zostaną wykonane przy implementacji tych endpointów.

## Weryfikacja
Testy API: anonimowy dostęp, CSRF, role, obce identyfikatory, zmiana roli i odebranie dostępu w istniejącej sesji, wycofanie tworzenia.
Testy PostgreSQL TransactionTestCase: współbieżna degradacja/usunięcie Owner, ponowne sprawdzenie roli po oczekiwaniu na blokadę.
Cel P95 i odbiór całego MVP pozostają w bolcie 008; bez deklaracji zmierzonej wydajności w tym etapie.

Źródła techniczne: [Django select_for_update](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update), [DRF permissions i filtrowanie list](https://www.django-rest-framework.org/api-guide/permissions/).
