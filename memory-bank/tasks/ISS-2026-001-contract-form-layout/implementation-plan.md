# Plan naprawy ISS-2026-001

## Cel

Wyrównać pionowo pola „Osoba umowy”, „Firma” i „Nazwa umowy” w formularzu dodawania umowy, zachowując przycisk „+ Nowa firma”, istniejące działanie formularza oraz responsywny układ.

## Kontekst i dowody

- Zgłoszenie: [ISS-2026-001](../../issues/ISS-2026-001/issue.md)
- Zrzut bazowy: [contract-form-layout.png](../../issues/ISS-2026-001/evidence/contract-form-layout.png)
- Komponent: `frontend/app/components/contract-form.tsx`
- Style: `frontend/app/globals.css`
- Istniejące testy: `frontend/tests/family.spec.ts`
- Kryterium produktu: `memory-bank/intents/002-family-income-management/units/002-family-management-ui/stories/002-contract-company-forms.md`
- Projekt dotyczy istniejącego formularza w ukończonym bolcie 011; nie dodaje nowego ekranu ani nowego przepływu.

## Diagnoza

W `.form-grid` komórka firmy zawiera standardowe pole oraz dodatkowy przycisk, więc wyznacza wyższy wiersz niż sąsiednie pola. Bezpośrednie elementy `.field` rozciągają się na wysokość tego wiersza, a ich wewnętrzny grid rozkłada wolną przestrzeń. Na dostarczonym zrzucie etykiety są zasadniczo wyrównane; różnica dotyczy kontrolek: selektor firmy ma około 49 px wysokości, a pola osoby i nazwy są rozciągnięte do około 78 px i zaczynają się około 30 px niżej. Diagnozę potwierdzić testem na bieżącym formularzu przed zmianą.

## Zakres implementacji

1. Dodać wąskie reguły CSS dla pól w siatce formularza umowy: utrzymać bezpośrednie `.field` przy górnej krawędzi wiersza (`#contract-form .form-grid > .field { align-self: start; }`) oraz ustawić spójną wysokość 46 px na polach input/select. Test bazowy potwierdził przesunięcie o 27 px; po samym wyrównaniu górnych krawędzi natywne wymiary różniły się o 2 px (44 vs. 46), dlatego wysokość zostanie ujednolicona.
2. Nie zmieniać globalnego zachowania `.field`, rozmiarów kolumn, przycisku dodawania firmy ani logiki formularza.
3. Dodać regresyjne sprawdzenie Playwright w `frontend/tests/family.spec.ts`, jawnie przy viewport 1440 px (>1200 px): porównać górne krawędzie i wysokości kontrolek trzech pól z tolerancją 1 px, uwzględnić minimalną wysokość 44 px oraz brak nachodzenia przycisku „+ Nowa firma” na pole lub kolejny rząd. Test ma nie przejść przed CSS i przejść po CSS.
4. Zachować zrzut otwartego formularza przed zmianą przy 1440 px, a po zmianie przy 1440 i 390 px. Sprawdzić też istniejący układ przy 1024 px (dwie kolumny, więc pola z pierwszego rzędu nie muszą mieć wspólnego y), mobile 390 px, szybkie dodawanie firmy, fokus/Escape, walidację pierwszego rzędu oraz długą nazwę firmy. Nie duplikować istniejących przepływów testowych.

## Poza zakresem

Zmiany treści, walidacji, dostępności semantycznej, backendu, układu innych formularzy i nowego widoku UI.

## Weryfikacja po akceptacji planu

- Prettier na zmienionych plikach TSX/CSS, następnie sprawdzenie formatowania.
- ESLint dla zmienionego testu/komponentu oraz Stylelint dla CSS.
- Odpowiedni Playwright `family.spec.ts` i kontrola widoku desktop/mobile.
- `scripts/quality.ps1`, przegląd diffu oraz `git diff --check`.
- Zaktualizować zgłoszenie o przyczynę, poprawkę, commit i dowód weryfikacji.

## Wynik implementacji

Wdrożono scoped `align-self: start` oraz wysokość 46 px dla kontrolek w gridzie formularza. Test bazowy odtworzył 27 px różnicy; po poprawce `family.spec.ts` przeszedł 17/17. Zapisano dowody 1440/1024/390 px i walidacji. Prettier, ESLint, Stylelint i TypeScript zmienionego zakresu przeszły. Pełny `scripts/quality.ps1` zatrzymał się na 32 niezmienionych plikach; nie rozszerzano zakresu.

## Status review i implementacji

Niezależny reviewer `@_reviewer` zaakceptował plan oceną 8,8/10 dnia 2026-10-07. Po akceptacji wdrożono CSS i test regresyjny. Implementacja przeszła `family.spec.ts` 17/17, ukierunkowany test geometrii oraz responsywność 1440/1024/390 px. Prettier, ESLint, Stylelint i TypeScript zmienionego zakresu przeszły. Pełny `scripts/quality.ps1` zatrzymał się na 32 niezmienionych plikach repozytorium zgłoszonych przez Prettier; nie formatowano niepowiązanego zakresu.
