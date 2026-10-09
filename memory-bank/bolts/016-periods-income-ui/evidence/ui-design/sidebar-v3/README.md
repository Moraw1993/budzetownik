---
bolt: 016-periods-income-ui
version: sidebar-v3
created: "2026-10-09T06:04:41Z"
status: awaiting-user-checkpoint
---

# Projekt UI bolta 016 — sidebar-v3

Istniejący sidebar i topbar pozostają podstawą. Pięć wcześniejszych kanw było wyłącznie zapoznawcze. Niniejsze pliki są odizolowaną wizualizacją Plan, bez połączenia z API i bez wdrożenia do aplikacji.

[Plan implementacji](../../../implementation-plan.md) · [Niezależna ocena](review.md) · [Historia odrzuconej v2](../sidebar-v2/review.md).

## Pięć ekranów

| Ekran                | Podgląd HTML                         | Desktop 1440 CSS                       | Mobile 390 CSS                        |
| -------------------- | ------------------------------------ | -------------------------------------- | ------------------------------------- |
| Lata                 | [years.html](years.html)             | [obraz](captures/years-1440.jpg)       | [obraz](captures/years-390.jpg)       |
| Miesiące             | [months.html](months.html)           | [obraz](captures/months-1440.jpg)      | [obraz](captures/months-390.jpg)      |
| Formularz przychodu  | [income.html](income.html)           | [obraz](captures/income-1440.jpg)      | [obraz](captures/income-390.jpg)      |
| Lista i podsumowanie | [summary.html](summary.html)         | [obraz](captures/summary-1440.jpg)     | [obraz](captures/summary-390.jpg)     |
| Załączniki           | [attachments.html](attachments.html) | [obraz](captures/attachments-1440.jpg) | [obraz](captures/attachments-390.jpg) |

Każda strona zawiera oddzielnie oznaczone warianty. Pasek „Podglądy ekranów”, żółta informacja i stos wariantów należą wyłącznie do narzędzia oceny; nie są projektem nowej nawigacji produkcyjnej. Prototyp używa systemowego fallback font; produkcyjny Geist pozostaje wymaganiem.

## Poprawki po review v2

- R1: [nieznany wynik zapisu](captures/I-unknown-1440.jpg) i [mobile](captures/I-unknown-390.jpg); jedna świadoma próba z tym samym kluczem/payloadem; brak uploadu do potwierdzenia.
- R2: [porównanie konfliktu](captures/I-conflict-1440.jpg), [mobile](captures/I-conflict-390.jpg), [ręczne połączenie](captures/I-merge-390.jpg) i [edycja powiązań](captures/I-edit-390.jpg).
- P3: [poprawne usunięcie pliku](captures/A-removed-390.jpg), [długa nazwa](captures/A-long-390.jpg) i [duża kwota](captures/S-boundary-390.jpg).

Screenshoty przechwycił główny agent udokumentowanym CUA. Recenzent ocenia je niezależnie; raport ujawnia ograniczenia jego przeglądarki. Nie są to testy aplikacji ani dowód działania API.

## Weryfikacja

- scripts/quality.ps1: PASS — Ruff 91 plików, Prettier, ESLint, Stylelint, TypeScript i narzędzia probe.
- Scoped Prettier dla HTML/CSS/JSON i Stylelint CSS: PASS; nie zmieniono reguł.
- Kontrola pięciu HTML: 158 lokalnych linków i 55 unikalnych identyfikatorów, bez braków/duplikatów.
- [Pomiary CUA](captures/metrics.json): rzeczywisty clientWidth 1440/390, równy scrollWidth; brak overflow całej strony. Ustawienia viewport IAB skorygowano o zoom, zapisując oba wymiary.
- Format i linki dokumentacji oraz diff sprawdzane przed commitem. Testów funkcjonalnych Django/Playwright nie uruchamiano dla samych makiet; istniejący frontend/backend nie został zmieniony.

## Checkpoint

Niezależny reviewer zaakceptował wszystkie pięć widoków (8,4–8,5/10) i pomocnicze panele (>7,5). Oczekujemy jawnej zgody użytkownika na sidebar-v3 i Plan bolta 016. Bolt pozostaje in-progress/current_stage plan do tego checkpointu. Następna faza Implement zaczyna się dopiero po zgodzie.
