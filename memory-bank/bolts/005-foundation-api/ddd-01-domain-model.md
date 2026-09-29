---
unit: 002-foundation-api
bolt: 005-foundation-api
stage: model
status: complete
updated: 2026-09-11T19:55:30+02:00
---

# Static Model - Foundation API: members, income and audit

## Bounded Context

Kontekst **Household Records** opisuje członków gospodarstwa niezależnych od
kont użytkowników, ich konfigurowalne relacje rodzinne oraz deklarowane źródła
dochodu. Kontekst **Audit** zapisuje niezmienialny ślad udanych zmian źródeł
dochodu. Autoryzacja i aktywne członkostwo użytkownika pozostają w istniejącym
kontekście Household Access (ADR-002); role rodzinne nie przyznają uprawnień.

## Domain Entities

| Entity | Properties | Business Rules |
| --- | --- | --- |
| `HouseholdMember` | household, optional account, display name, relation type, active flag, deactivated timestamp | Należy do jednego gospodarstwa; może istnieć bez konta; konto musi być użytkownikiem tego samego gospodarstwa i może wskazywać najwyżej jednego członka w tym gospodarstwie; dezaktywacja nie usuwa źródeł ani historii. |
| `RelationType` | household, name, active flag, deactivated timestamp | Słownik jest prywatny dla gospodarstwa; utworzyć i zmienić go może Owner lub Administrator; używany typ jest dezaktywowany zamiast niszczony. |
| `IncomeSource` | household, optional member, name, category, payer, start/end dates, default monthly amount, currency, frequency, regular flag, description, active flag, deactivated timestamp | Należy do dokładnie jednego gospodarstwa; opcjonalny członek musi należeć do tego samego gospodarstwa; kwota jest dziesiętna; nie tworzy transakcji ani przychodu za miesiąc; dezaktywacja zachowuje dane. |
| `AuditLog` | household, actor, action, object type/id, occurred at, before state, after state | Jest tylko do odczytu przez zwykłe API; dla utworzenia, zmiany i dezaktywacji źródła zapisuje się w tej samej transakcji; nigdy nie zawiera haseł, ciasteczek ani tokenów. |

## Value Objects

| Value Object | Properties | Constraints |
| --- | --- | --- |
| `Money` | decimal amount, ISO currency code | Kwota jest skończoną wartością dziesiętną, nie liczbą zmiennoprzecinkową; waluta jest zachowana przy odczycie. |
| `IncomeSchedule` | frequency, is regular, start date, optional end date | Częstotliwość jest wartością ze słownika; data końcowa nie może poprzedzać daty rozpoczęcia. |
| `AuditSnapshot` | serializowalne pola before/after | Zawiera tylko dozwolone pola domenowe; pola sekretów są wykluczone. |

## Aggregates

| Aggregate Root | Members | Invariants |
| --- | --- | --- |
| `Household` | HouseholdMember, RelationType, IncomeSource, AuditLog | Wszystkie encje należą do tego samego gospodarstwa; kontekst dostępu jest ponownie sprawdzany przy zapisie; modyfikować mogą wyłącznie Owner i Administrator. |
| `IncomeSource` | IncomeSchedule, AuditSnapshot dla operacji | Tworzenie, zmiana albo dezaktywacja źródła i odpowiadający im `AuditLog` są atomowe; nie istnieje operacja trwałego usunięcia w publicznym API. |

## Domain Events

| Event | Trigger | Payload |
| --- | --- | --- |
| `HouseholdMemberCreated` | Owner/Administrator dodaje członka | household id, member id, actor id. |
| `HouseholdMemberDeactivated` | Członek przechodzi do stanu archiwalnego | household id, member id, actor id, occurred at. |
| `RelationTypeDeactivated` | Używany typ relacji nie jest już aktywny | household id, relation type id, actor id. |
| `IncomeSourceCreated` | Utworzono źródło dochodu | household id, source id, actor id, sanitized after state. |
| `IncomeSourceChanged` | Zmieniono źródło dochodu | household id, source id, actor id, sanitized before/after states. |
| `IncomeSourceDeactivated` | Źródło dochodu przeszło do stanu nieaktywnego | household id, source id, actor id, sanitized before/after states. |

## Domain Services

| Service | Operations | Dependencies |
| --- | --- | --- |
| `HouseholdMemberService` | tworzenie, edycja, dezaktywacja, bezpieczne powiązanie konta | Household access policy, member repository. |
| `RelationTypeService` | tworzenie, aktualizacja, dezaktywacja słownika relacji | Household access policy, relation type repository. |
| `IncomeSourceService` | tworzenie, edycja, dezaktywacja źródeł z audytem | Household access policy, income source repository, audit writer, transaction boundary. |
| `AuditWriter` | tworzenie zredagowanego wpisu audytowego w transakcji | Audit repository, audit snapshot sanitizer. |

## Repository Interfaces

| Repository | Entity | Methods |
| --- | --- | --- |
| `HouseholdMemberRepository` | HouseholdMember | list_active(household), get_for_household(household, id), account_is_linked(household, account), save(member). |
| `RelationTypeRepository` | RelationType | list_active(household), get_for_household(household, id), save(type). |
| `IncomeSourceRepository` | IncomeSource | list_for_household(household), get_for_household(household, id), save(source). |
| `AuditLogRepository` | AuditLog | append(entry), list_for_household(household, filters). |

## Ubiquitous Language

| Term | Definition |
| --- | --- |
| Gospodarstwo | Granica własności danych i autoryzacji dla członków, słowników, źródeł oraz audytu. |
| Członek | Osoba opisana w gospodarstwie; nie jest tożsama z kontem ani z członkostwem użytkownika w aplikacji. |
| Powiązanie konta | Opcjonalne wskazanie konta użytkownika przez członka tego samego gospodarstwa. |
| Typ relacji | Konfigurowalna, nieuprawnieniowa etykieta rodzinna, np. rodzic lub dziecko. |
| Źródło dochodu | Deklaracja parametrów dochodu, nie miesięczny przychód ani transakcja. |
| Dezaktywacja | Odwracalne logiczne wyłączenie encji bez niszczenia danych i historii. |
| Audyt | Niezmienialny zapis udanej operacji z wykonawcą, czasem, obiektem i zredagowanymi stanami przed/po. |
