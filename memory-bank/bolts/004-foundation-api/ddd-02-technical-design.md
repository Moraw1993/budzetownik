---
stage: design
bolt: 004-foundation-api
created: 2026-09-11T19:16:30+02:00
---

# Projekt techniczny zaproszeń

## Architektura i odpowiedzialności

Rozszerzenie istniejącej aplikacji Django `households` zachowuje podział z boltów 002–003: modele i ograniczenia danych, selektory odczytu, transakcyjne usługi przypadków użycia, serializatory i cienkie widoki DRF. Nie powstaje osobna usługa ani repozytorium abstrakcyjne.

- `households/models.py`: encja `Invitation`, ograniczenia bazy oraz indeksy.
- `households/selectors.py`: listowanie i odczyt zaproszeń wyłącznie w zakresie gospodarstwa wykonawcy.
- `households/services.py`: wystawienie, odwołanie i przyjęcie pod kontrolą transakcji.
- `households/serializers.py`: walidacja ról, danych nowego konta i tokenu; odpowiedzi nie zawierają skrótu tokenu.
- `households/views.py`: endpointy HTTP, CSRF i konwersja wyników usług na odpowiedzi.
- `households/tests/`: testy API, uprawnień oraz współbieżności.

## Kontrakt API

Wszystkie endpointy gospodarstwa wymagają sesji i CSRF dla metod zmieniających dane. Adresy z `household_id` stosują reguły ADR-002: brak dostępu i nieistniejący zasób zwracają ten sam `404`; niewystarczająca rola w dostępnym gospodarstwie zwraca `403`.

- `GET /api/households/{household_id}/invitations/`: tylko Owner; zwraca listę `{id, role, created_at, expires_at, revoked_at, accepted_at}` własnego gospodarstwa, bez tokenu i jego skrótu.
- `POST /api/households/{household_id}/invitations/`: tylko Owner; wejście `{role}`; zwraca `201` z metadanymi zaproszenia i `invitation_url` tylko w tej odpowiedzi. `role` jest jedną z ról gospodarstwa.
- `DELETE /api/households/{household_id}/invitations/{invitation_id}/`: tylko Owner; odwołuje nieprzyjęte zaproszenie i zwraca `204`. Zaproszenie przyjęte nie może wrócić do stanu aktywnego.
- `POST /api/invitations/accept/`: endpoint obsługiwany przez stronę lokalnego frontendu, która odczytuje token z fragmentu URL i przesyła go w JSON, nie w ścieżce. Dla zalogowanego użytkownika wejście to `{token}`; dla osoby bez sesji `{token, username, password}`. Ważny token skutkuje członkostwem z rolą zaproszenia; odpowiedź nie zwraca tokenu. Nieważny, odwołany, wygasły lub zużyty token zwraca jednolity błąd walidacji bez metadanych gospodarstwa.

Link ma postać `https://localhost:8443/accept-invitation#{token}`. Fragment nie jest wysyłany w żądaniu HTTP do frontendu, co ogranicza ujawnienie w logach serwera i nagłówku Referer. Frontend przekazuje sekret wyłącznie w treści żądania POST przez lokalny HTTPS.

## Trwałość danych i współbieżność

Model `Invitation` zawiera:

- UUID, `household` i `issued_by` jako klucze obce;
- `role` z tymi samymi wyborami co `HouseholdUser`;
- unikalny `token_hash`, `created_at`, `expires_at`, opcjonalne `revoked_at`, `accepted_at` i `accepted_by`;
- indeksy dla `household` z czasami/statusami używanymi przy listowaniu;
- ograniczenie spójności, że `accepted_at` i `accepted_by` są ustawione razem albo oba pozostają puste.

Token jest generowany przez kryptograficznie bezpieczny generator. Przechowywany jest skrót HMAC-SHA-256 z kluczem aplikacji; usługa porównuje go bezpiecznie czasowo. Token nigdy nie jest zapisywany w modelu, odpowiedziach po wystawieniu, logach ani wpisach audytu.

Wystawienie i odwołanie działają w `transaction.atomic()` po zablokowaniu `Household`, a następnie ponownym sprawdzeniu roli Ownera. Przyjęcie najpierw wyszukuje kandydata po skrócie bez zwracania danych na zewnątrz, następnie w jednej transakcji blokuje kolejno `Household` i `Invitation`, ponownie weryfikuje skrót oraz ważność i dopiero wtedy tworzy albo pobiera członkostwo. Ta kolejność jest zgodna z ADR-002 i zapobiega dwukrotnemu zużyciu podczas równoległych żądań.

Utworzenie nowego konta, członkostwa i oznaczenie przyjęcia stanowią jedną transakcję. Ograniczenie unikalności `(household, user)` pozostaje ostatnią ochroną przed duplikatem; gdy członkostwo już istnieje, jego rola nie jest zmieniana.

## Bezpieczeństwo i błędy

- Sesja Django i CSRF obowiązują zgodnie z ADR-001. Endpoint przyjęcia uzyskuje token CSRF podczas załadowania lokalnej strony i wymaga go także dla rejestracji anonimowej.
- `invitation_url` może być przedstawiony tylko Ownerowi w odpowiedzi na utworzenie. Endpointy listy i szczegółu nigdy nie ujawniają sekretu.
- Logowanie aplikacyjne usuwa token z payloadu, adresów i komunikatów wyjątków. Zdarzenia wystawienia, odwołania i powodzenia/odrzucenia przyjęcia są rejestrowane bez sekretu; pełny model audytu zmian pozostaje zakresem bolta 005.
- Błędne dane wejściowe zwracają `400`; nieprawidłowy token zwraca ogólny `400`; konflikt niezmienników bazy lub wyścig nie może skutkować częściowym kontem albo członkostwem.
- Brak wysyłki e-maili, zewnętrznego dostawcy tożsamości i publicznego wejścia z sieci — link jest przeznaczony dla lokalnego hosta.

## Weryfikacja projektu

Testy implementacyjne obejmą:

- wystawienie z rolą i terminem dokładnie siedem dni oraz jednorazowe ujawnienie linku;
- odmowę wystawienia, listowania i odwołania dla Administratora, Membera, Viewera, anonimowego użytkownika i osoby spoza gospodarstwa;
- niewidoczność zaproszeń obcego gospodarstwa oraz brak tokenu w odpowiedziach i zdarzeniach;
- przyjęcie przez istniejące konto oraz utworzenie konta przez ważny link;
- odrzucenie tokenu wygasłego, odwołanego i już zużytego bez trwałych zmian;
- dwa równoległe przyjęcia tego samego linku: najwyżej jedno zużycie i jedno nowe członkostwo;
- istniejące członkostwo: bez duplikatu i bez zmiany roli.

Cel wydajności P95 oraz odbiór całego MVP pozostają w bolcie 008; ten bolt nie deklaruje pomiaru wydajności.
