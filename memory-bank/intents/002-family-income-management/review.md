# Plan intentu 002 — do przeglądu

## Decyzje użytkownika

- „Zarządzanie rodziną” skupia członków oraz przypisane im umowy i źródła; źródła mogą należeć też do gospodarstwa.
- Przychód za miesiąc powstanie dopiero przy przyszłej karcie miesiąca przez wybór osoby albo gospodarstwa, powiązanego źródła i rzeczywistej kwoty.
- Kwota umowy jest brutto i ma podstawę miesięczną, godzinową lub za całość.
- Firma w pierwszej wersji wymaga tylko nazwy. Typy umów: praca, zlecenie, dzieło i inne.
- Domyślna miesięczna kwota innego źródła jest opcjonalną podpowiedzią.

## Model i migracja

`IncomeSource` pozostaje wspólną tożsamością wybieraną w przyszłej karcie miesiąca. `Contract` przechowuje szczegóły umowy 1:1 do źródła, a `Company` jest słownikiem gospodarstwa. Stare źródła pozostają typu `other`; nie powstaje umowa ani przychód na podstawie samej nazwy „Wynagrodzenie”. Jawne przekształcenie wymaga uzupełnienia danych umowy i zachowuje identyfikator źródła.

## Jednostki i kolejność

| Krok | Jednostka i bolt | Wynik | Stories |
| --- | --- | --- | ---: |
| 1 | [API i migracja — 010](../../bolts/010-family-income-api/bolt.md) | Firma, umowa, inne źródła, zachowanie starych danych, audyt. | 4 |
| 2 | [Interfejs — 011](../../bolts/011-family-management-ui/bolt.md) | Nowy dział i formularze. | 3 |
| 3 | [Odbiór — 012](../../bolts/012-family-income-acceptance/bolt.md) | Migracja, role, izolacja i pełny scenariusz lokalny. | 2 |

Prace w kodzie zaczynają się po zakończeniu [008-local-acceptance](../../bolts/008-local-acceptance/bolt.md). Bolt 009 pozostaje w bieżącym etapie testów. Szczegóły zmian plików zawiera [podział jednostek](units.md), a kompletne kryteria [wymagania](requirements.md) i [pokrycie](traceability.md).

## Granica tego planu

Plan obejmuje 7 FR, 3 NFR, 3 jednostki, 9 stories i 3 bolty. Nie dodaje tabeli miesięcznych przychodów ani obliczania wypłaty netto. Obecny audyt ma zachować historię zmian umów; sposób utrwalania danych źródła w przyszłym zapisie miesiąca pozostaje decyzją przyszłego etapu.

## Status

Artefakty przygotowane do przeglądu użytkownika. Inception nie jest jeszcze oznaczone jako ukończone i żaden nowy bolt nie został uruchomiony.
