---
bolt: 013-periods-api
created: 2026-10-07T10:16:53Z
status: accepted
superseded_by: null
---

# ADR-006: Wspólna blokada roku dla zapisów finansowych

## Context

Stan miesiąca decyduje, czy można zapisywać dane finansowe przypisane do tego okresu. Zamykanie miesiąca nie może ścigać się z równoległym utworzeniem, edycją ani usunięciem przychodu: po zatwierdzonym zamknięciu żaden późniejszy zapis przychodu nie może przejść na podstawie nieaktualnego odczytu stanu. `AccountingYear` jest agregatem zawierającym komplet dwunastu miesięcy, a okresy i przychody są implementowane w osobnych boltach.

ADR-002 wymaga blokowania agregatu oraz ponownej weryfikacji członkostwa i roli po uzyskaniu blokady. ADR-004 wymaga atomowego zapisu zmiany finansowej i jej audytu. Potrzebny jest jawny kontrakt blokowania wspólny dla API okresów i przyszłego API przychodów.

## Decision

Operacja zmieniająca stan miesiąca i każda operacja zapisująca przychód najpierw blokują ten sam wiersz `AccountingYear` przez `select_for_update()` i wykonują sprawdzenie oraz zapis w jednej transakcji bazodanowej.

Operacja przychodu po uzyskaniu blokady ponownie sprawdza aktualne członkostwo i rolę zgodnie z ADR-002, odczytuje stan miesiąca pod tą samą blokadą i zapisuje przychód tylko wtedy, gdy miesiąc jest `active`. Zmiana stanu miesiąca weryfikuje dozwolone przejście i zapisuje je razem z niezmiennym wpisem audytu zgodnie z ADR-004. Kolejność uzyskania blokady rozstrzyga wyścig: zapis przychodu może zakończyć się przed zatwierdzeniem zamknięcia albo zostać odrzucony po nim.

Blokada obejmuje jeden agregat roku. Zapis w jednym roku nie wymaga blokady innych lat tego gospodarstwa. Operacje nie wykonują wywołań sieciowych ani plikowych, gdy trzymają blokadę.

## Rationale

Wspólny wiersz agregatu daje obu niezależnym kontekstom ten sam punkt synchronizacji i chroni regułę zamkniętego miesiąca bez rozproszonej transakcji. Zakres roczny jest zgodny z granicą agregatu ustanowioną dla kompletności dwunastu miesięcy. Domowe aplikacje mają małą współbieżność, więc krótkie transakcje powinny utrzymać koszt serializacji na akceptowalnym poziomie.

### Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
|-------------|------|------|--------------|
| Blokować wyłącznie wiersz miesiąca | Większa równoległość zapisów w różnych miesiącach | Rozprasza synchronizację poza zdefiniowaną granicę agregatu i wymaga wspólnej dyscypliny blokowania miesiąca w każdym kontekście | Używamy wiersza korzenia agregatu jako jawnego kontraktu między boltami |
| Odczytać stan bez blokady i sprawdzić go ponownie po zapisie | Mniej oczekiwania na blokady | Pozostawia trudny do zagwarantowania wyścig między końcową kontrolą a zatwierdzeniem zamknięcia | Nie zapewnia wymaganej kolejności zatwierdzonych operacji |
| Blokować całe gospodarstwo dla każdego zapisu | Prosta wspólna blokada dla różnych domen | Niepotrzebnie serializuje niezależne lata i zwiększa zakres ADR-002 | Dla tego niezmiennika wystarcza agregat roku |

## Consequences

### Positive

- Zamknięcie miesiąca i zapis przychodu mają jednoznaczną kolejność zatwierdzenia.
- API okresów i przychodów współdzielą jawną regułę transakcyjną.
- Zapisy w różnych latach pozostają niezależne.

### Negative

- Operacje zapisu w tym samym roku czekają na siebie, także jeśli dotyczą różnych miesięcy.
- Każdy przyszły kontekst zapisujący dane zależne od stanu miesiąca musi stosować tę samą blokadę korzenia.

### Risks

- Pominięcie blokady przez którykolwiek endpoint może przywrócić wyścig. Testy integracyjne powinny sprawdzać kolejność zamknięcia i zapisu przychodu, a przegląd nowych przypadków użycia powinien weryfikować wspólny kontrakt.
- Dłuższe transakcje mogą zwiększyć opóźnienia. Transakcje muszą ograniczać się do operacji bazodanowych; należy monitorować cel P95 poniżej 500 ms.

## Related

- **Stories**: 001-create-year-months, 002-activate-month, 003-close-and-reopen-month; income write stories in bolt 014.
- **Standards**: `memory-bank/standards/git-workflow.md`, `memory-bank/standards/system-architecture.md`.
- **Previous ADRs**: ADR-002, ADR-004.
