---
unit: 002-family-management-ui
intent: 002-family-income-management
unit_type: frontend
default_bolt_type: simple-construction-bolt
phase: construction
status: in-progress
created: 2026-09-23T08:24:02Z
updated: 2026-09-29T20:51:49Z
---

# Interfejs zarządzania rodziną

## Cel i granica

Zebrać członków, umowy, inne źródła i źródła całego gospodarstwa w dziale „Zarządzanie rodziną”. Interfejs pokazuje dane i wywołuje API; reguły uprawnień oraz powiązań pozostają w backendzie. Nie dodaje przychodów do miesięcy.

## Wymagania przypisane

FR-01 jako właściciel. Widoczne zachowanie FR-02–FR-06 oraz stany odczytu z FR-07 są realizowane przez ten interfejs na podstawie API jednostki 001.

## Ekrany i przepływy

- Nawigacja gospodarstwa pokazuje „Zarządzanie rodziną” i zachowuje wybrane gospodarstwo po przejściu między sekcjami.
- Lista członków pokazuje źródła każdej osoby; osobny obszar pokazuje źródła całego gospodarstwa. Członek bez źródeł ma czytelny stan pusty.
- „Dodaj umowę” wybiera członka i firmę ze słownika, pozwala dodać firmę bez utraty formularza, zbiera typ umowy, daty, stanowisko gdy właściwe, kwotę brutto, podstawę i walutę.
- „Dodaj inne źródło dochodu” wybiera osobę albo całe gospodarstwo; domyślna kwota miesięczna jest opcjonalną podpowiedzią.
- Lista i formularze odróżniają kwotę brutto umowy od podpowiedzi przy innym źródle. Nie pokazują żadnej z nich jako przychodu miesiąca.
- Istniejące źródło może zostać jawnie przekształcone w umowę po podaniu wymaganych danych. Nie zmienia się samo na podstawie nazwy lub kategorii.
- Owner i Administrator widzą akcje zmiany, Member i Viewer odczyt. Błędy API i walidacji są prezentowane przy odpowiednich polach.

## Granice komponentów

W bolcie należy ocenić ponowne użycie obecnych `MembersPanel`, `IncomePanel`, `ActionForm`, pól formularza i tabel. Nowa kompozycja strony może korzystać z tych komponentów po rozdzieleniu formularza umowy i źródła; nie kopiować obsługi żądań ani stylów. Typy odpowiedzi i żądań trafiają do `frontend/app/lib/api.ts`.

## Stories

- [001-family-navigation](stories/001-family-navigation.md)
- [002-contract-company-forms](stories/002-contract-company-forms.md)
- [003-other-source-and-conversion](stories/003-other-source-and-conversion.md)

Łącznie 3 stories Must; wszystkie zaplanowane w bolcie 011.

## Bolt i zależności

Bolt [011-family-management-ui](../../../../bolts/011-family-management-ui/bolt.md) po 010-family-income-api. Nie zmienia trwającego bolta 009 ani jego testów.

## Kryteria zakończenia

- Scenariusze tworzenia, edycji i archiwizacji źródeł działają dla obu typów właściciela.
- Formularze pozostają czytelne na szerokim, pośrednim i mobilnym widoku oraz obsługiwane klawiaturą.
- Widok odczytu nie oferuje działań zmieniających dane; API wciąż egzekwuje role.
