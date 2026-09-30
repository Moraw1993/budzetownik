---
intent: 002-family-income-management
created: 2026-09-23T08:15:53Z
completed: 2026-09-30T07:30:17Z
status: complete
---

# Inception Log: Zarządzanie rodziną, umowami i źródłami dochodu

## Zakres

Rozszerzenie działającego fundamentu o firmy, umowy członków i inne źródła dochodu oraz nową organizację ekranów. Użytkownik zgłosił, że obecne „Wynagrodzenie” łączy pojęcia, które powinny być rozdzielone. Przychody za miesiąc należą do późniejszego etapu.

## Artefakty

| Artefakt | Status | Plik |
| --- | --- | --- |
| Wymagania | Zakres zrealizowany | requirements.md |
| Kontekst | Podstawa zrealizowanego zakresu | system-context.md |
| Jednostki | 3 ukończone | units.md i unit-brief.md |
| Stories | 9 ukończonych | units/*/stories/*.md |
| Bolty | 3 ukończone | 010–012 w memory-bank/bolts |
| Pokrycie i plan | Zweryfikowane odbiorem 012 | traceability.md, review.md |

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

Construction zakończono po zatwierdzeniu raportu bolta 012 i uruchomieniu obowiązkowego skryptu zamknięcia. Integracja do develop i Operations są odrębnymi operacjami; ich stan opisuje [raport domknięcia](../../operations/post-bolt-012.md). Status complete nie oznacza opublikowanego wydania ani wdrożenia produkcyjnego.
