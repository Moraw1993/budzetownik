---
stage: model
bolt: 004-foundation-api
created: 2026-09-11T19:12:05+02:00
---

# Model domeny zaproszeń

## Bounded context

Zaproszenie daje wskazanemu posiadaczowi linku jednorazową możliwość dołączenia do jednego gospodarstwa bez wysyłki e-maila. Należy do kontekstu `households`, korzysta z istniejących kont `auth` i tworzy wyłącznie istniejące członkostwo `HouseholdUser`. Nie tworzy członka rodziny ani nie zmienia zasad ról z ADR-002.

## Encje

- **Invitation**: identyfikator, gospodarstwo, proponowana rola, skrót nieprzewidywalnego tokenu, czas utworzenia, czas wygaśnięcia, czas odwołania oraz czas i identyfikator przyjęcia. Należy do dokładnie jednego gospodarstwa; oryginalny token istnieje wyłącznie podczas utworzenia i przekazania w linku.
- **Household**: istniejący agregat określający granicę dostępu. Wystawienie, odwołanie i przyjęcie zaproszenia są operacjami w jego zakresie.
- **HouseholdUser (członkostwo)**: istniejące powiązanie konta z gospodarstwem i rolą. Para `household`–`user` jest unikalna; przyjęcie nie tworzy drugiego powiązania ani nie zmienia roli istniejącego.
- **User**: istniejące konto. Osoba bez konta może je utworzyć w toku przyjęcia ważnego zaproszenia; osoba z kontem uwierzytelnia się istniejącą sesją.

## Obiekty wartości

- **InvitationToken**: nieprzewidywalny, jednorazowy sekret przekazany w linku. W bazie przechowywany i porównywany jest wyłącznie jego jednokierunkowy skrót; sekret nie trafia do odpowiedzi poza wystawieniem, logów ani audytu.
- **InvitationRole**: jedna z zatwierdzonych ról gospodarstwa (`Owner`, `Administrator`, `Member`, `Viewer`). Nie jest rolą rodzinną ani uprawnieniem technicznego administratora Django.
- **InvitationValidity**: wynik oceny zaproszenia względem czasu i stanu: ważne tylko przed upływem terminu oraz bez odwołania i wcześniejszego przyjęcia.

## Agregaty i niezmienniki

### Household jako granica agregatu

Zapisy dotyczące dostępu używają tej samej granicy i blokady `Household`, które definiuje ADR-002. Po uzyskaniu blokady ponownie sprawdzana jest aktualna rola wykonawcy.

- Tylko aktualny `Owner` może wystawić lub odwołać zaproszenie w swoim gospodarstwie.
- Zaproszenie ma rolę i termin ważności dokładnie siedem dni od utworzenia.
- Lista i szczegóły zaproszeń są filtrowane przez członkostwo w tym samym gospodarstwie; zasób spoza zakresu nie ujawnia swojego istnienia.
- Odwołane, wygasłe i przyjęte zaproszenie nie może stworzyć konta ani członkostwa.
- Przyjęcie blokuje odpowiednie gospodarstwo i zaproszenie w jednej transakcji, po czym ponownie ocenia ważność. Tylko jedna równoległa operacja może zapisać przyjęcie.
- Przyjęcie przez konto już należące do gospodarstwa nie tworzy duplikatu i nie zmienia jego roli. Zaproszenie jest wtedy zużywane tylko w ramach poprawnie zakończonej transakcji; ponowne otwarcie tego samego linku nie jest kolejnym przyjęciem.
- Niepowodzenie utworzenia konta lub członkostwa wycofuje zużycie zaproszenia; nie może pozostać zaproszenie oznaczone jako przyjęte bez wyniku operacji.

## Zdarzenia domenowe

- **InvitationIssued**: Owner wystawił zaproszenie; dane audytu zawierają wykonawcę, gospodarstwo, identyfikator zaproszenia, rolę i termin — bez tokenu.
- **InvitationRevoked**: Owner odwołał jeszcze nieprzyjęte zaproszenie; dane audytu zawierają wykonawcę i identyfikator zaproszenia.
- **InvitationAccepted**: ważne zaproszenie zostało zużyte i utworzono albo potwierdzono członkostwo; dane zawierają gospodarstwo, konto i zaproszenie, bez sekretu.
- **InvitationAcceptanceRejected**: próba użycia nieważnego linku nie zmienia stanu. Zdarzenie bezpieczeństwa może zawierać wyłącznie bezpieczny identyfikator/kontekst techniczny, nigdy token.

## Usługi domenowe

- **InvitationIssuanceService**: po potwierdzeniu roli Owner generuje sekret, tworzy zaproszenie z terminem `utworzenie + 7 dni` i zwraca link tylko w chwili wystawienia.
- **InvitationRevocationService**: odwołuje zaproszenie należące do wskazanego gospodarstwa po sprawdzeniu Ownera.
- **InvitationAcceptanceService**: w transakcji weryfikuje sekret i ważność, obsługuje konto istniejące albo utworzenie nowego, zapewnia idempotencję członkostwa i oznacza zaproszenie jako przyjęte dopiero po powodzeniu.
- **InvitationTokenService**: generuje sekret o odpowiedniej entropii, wylicza skrót i wykonuje porównanie bez ujawniania sekretu.
- **HouseholdAccessPolicy**: istniejąca polityka `read`, `edit_data`, `manage_access`; dla zaproszeń wymaga `manage_access` aktualnego Ownera.

## Dostęp do danych

W tym modularnym monolicie granicę dostępu realizują selektory i usługi Django ORM, zgodnie z poprzednimi boltami; nie wprowadza się sztucznej abstrakcji repozytorium.

- **InvitationSelector**: pobranie listy lub szczegółu wyłącznie w ramach gospodarstwa dostępnego dla wykonawcy.
- **InvitationWriter**: utworzenie, odwołanie i atomowe przyjęcie z blokadami wymaganymi przez agregat.
- **MembershipWriter**: utworzenie lub odczyt istniejącego członkostwa z ograniczeniem unikalności `(household, user)`.

## Język wszechobecny

- **Zaproszenie**: rekord dający jednorazową możliwość dołączenia do gospodarstwa; nie jest kontem ani członkiem rodziny.
- **Link zaproszenia**: lokalny link zawierający token; nie działa jako zdalny mechanizm dostępu poza komputerem hostującym aplikację.
- **Wystawienie**: utworzenie zaproszenia przez Ownera i jednorazowe udostępnienie linku.
- **Odwołanie**: trwałe unieważnienie nieprzyjętego zaproszenia.
- **Przyjęcie**: atomowe użycie ważnego zaproszenia prowadzące do członkostwa konta.
- **Zużyte zaproszenie**: zaproszenie, którego przyjęcie już się powiodło; nie może być użyte ponownie.
- **Ważne zaproszenie**: nieodwołane, niezużyte i niewygasłe w momencie kontroli w transakcji.
