---
intent: 002-family-income-management
created: 2026-09-23T08:15:53Z
completed: null
status: in-progress
---

# Inception Log: Zarządzanie rodziną, umowami i źródłami dochodu

## Zakres

Rozszerzenie działającego fundamentu o firmy, umowy członków i inne źródła dochodu oraz nową organizację ekranów. Użytkownik zgłosił, że obecne „Wynagrodzenie” łączy pojęcia, które powinny być rozdzielone. Przychody za miesiąc należą do późniejszego etapu.

## Artefakty

| Artefakt | Status | Plik |
| --- | --- | --- |
| Wymagania | Szkic do przeglądu | requirements.md |
| Kontekst | Do przeglądu | system-context.md |
| Jednostki | Do przeglądu | units.md i unit-brief.md |
| Stories | 9 do przeglądu | units/*/stories/*.md |
| Bolty | 3 zaplanowane, nierozpoczęte | 010–012 w memory-bank/bolts |
| Pokrycie i plan | Do przeglądu | traceability.md, review.md |

## Decyzje

- Członkowie mogą mieć wiele umów i innych źródeł dochodu.
- Źródło dochodu może należeć bezpośrednio do gospodarstwa.
- Kwota na umowie jest brutto i nie musi równać się przychodowi za miesiąc.
- Firma wymaga na start tylko nazwy; typy umów: praca, zlecenie, dzieło i inne.
- Kwota brutto umowy ma wybieraną podstawę (miesięczna, godzinowa lub za całość); kwota domyślna innego źródła jest opcjonalna.
- Dodawanie przychodu miesięcznego nastąpi później na karcie miesiąca przez wybór osoby lub gospodarstwa oraz powiązanego źródła.
- Istniejący bolt 009 zachowuje bieżący zakres; nowy model wymaga osobnego etapu.

## Podsumowanie planu

7 FR, 3 NFR, 3 jednostki, 9 stories i 3 bolty. Nowe bolty zależą od zakończenia 008-local-acceptance. Nie zmieniono kodu aplikacji.

## Następny krok

Przegląd zestawu artefaktów (checkpoint 3 procesu Inception). Po uwagach skorygować plan i dopiero wtedy oznaczyć Inception jako ukończone. Budowa nowego modelu pozostaje osobnym etapem.
