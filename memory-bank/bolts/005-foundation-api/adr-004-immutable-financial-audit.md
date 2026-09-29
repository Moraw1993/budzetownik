---
bolt: 005-foundation-api
created: 2026-09-11T20:04:43+02:00
status: accepted
superseded_by: null
---

# ADR-004: Niezmienialny audyt zmian danych finansowych

## Context

Źródła dochodu są pierwszymi obiektami finansowymi MVP, których utworzenie,
zmiana i dezaktywacja muszą pozostawiać ślad z wykonawcą, czasem, obiektem,
gospodarstwem i wartościami przed/po. Ten sam wymóg będzie dotyczył przyszłych
budżetów, kredytów i oszczędności. Audyt nie może utrwalić sekretów, a
nieudana operacja nie może wyglądać jak udana zmiana.

ADR-002 nakazuje utrzymywać kontekst gospodarstwa i aktualną rolę pod blokadą.
Standardy wymagają transakcyjności operacji wieloetapowych oraz historii zmian.

## Decision

Wprowadzamy wewnętrzną encję `AuditLog` z niemodyfikowalnymi wpisami. Usługa
zmieniająca źródło dochodu w jednej `transaction.atomic()` zapisuje zmianę
obiektu i wpis audytowy. Wpis zawiera `household`, wykonawcę, czas, akcję,
typ i identyfikator obiektu oraz zredagowane snapshoty przed/po z whitelisty
pól. Publiczne API oferuje tylko odczyt wpisów uprawnionemu Ownerowi i nie
udostępnia endpointów tworzenia, zmiany ani trwałego usuwania audytu.

## Rationale

Granica transakcji usuwa ryzyko trwałej zmiany bez historii albo historii
udającej zmianę, która została wycofana. Whitelista snapshotu zapobiega
przypadkowemu zapisywaniu haseł, ciasteczek i tokenów, także gdy model zostanie
rozszerzony w przyszłości. Jedna encja audytu daje spójny wzorzec kolejnym
modułom, bez przedwczesnego systemu zdarzeń i zewnętrznej infrastruktury.

### Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
| --- | --- | --- | --- |
| Log aplikacyjny zamiast trwałego audytu | Prosta implementacja | Brak spójnych danych do odczytu, retencja i format nie gwarantują historii | Nie spełnia FR-09 ani wymogu odczytu historii przez Ownera. |
| Sygnały Django zapisujące audyt poza usługą | Mniej kodu w przypadkach użycia | Trudniej kontrolować wykonawcę, kolejność transakcji i redakcję pól | Kontekst domenowy oraz integralność są zbyt niejawne. |
| Zewnętrzny, append-only event store | Silna specjalizacja audytu | Nowa usługa, operacyjna złożoność i rozproszona transakcja | Poza lokalnym zakresem MVP. |

## Consequences

### Positive

- Każda udana zmiana źródła ma spójny, możliwy do prześledzenia zapis.
- Wzorzec można zastosować do kolejnych encji finansowych bez zmiany granic bezpieczeństwa.
- Sekrety są chronione na wejściu do mechanizmu audytu, nie tylko w odpowiedzi API.

### Negative

- Każdy przypadek użycia zmieniający dane finansowe musi jawnie przekazać bezpieczny snapshot.
- Tabela audytu będzie rosła i w przyszłości wymaga polityki retencji lub eksportu.

### Risks

- Dodanie nowego wrażliwego pola może trafić do snapshotu, jeśli zostanie bezrefleksyjnie dopuszczone; ograniczeniem jest centralna whitelista i testy redakcji.

## Related

- **Stories**: 011-income-sources, 012-financial-audit, 013-preserve-history.
- **Standards**: coding-standards.md, system-architecture.md.
- **Previous ADRs**: ADR-001, ADR-002.
