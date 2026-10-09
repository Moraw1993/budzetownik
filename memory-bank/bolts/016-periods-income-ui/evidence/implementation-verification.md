# Weryfikacja implementacji 016

Branch feat/bolt-016-periods-income-ui, commit implementacji 3c0d1b5 i bazowy fragment 0e13ec5. Baza develop: 29fc7e3744e11c3a8c48932e816ca2d4e01a59b8. Użytkownik zaakceptował sidebar-v3 komendą „rozpocznij implementacje”.

## Wyniki

| Sprawdzenie            | Wynik                          | Zakres                                                  |
| ---------------------- | ------------------------------ | ------------------------------------------------------- |
| scripts/quality.ps1    | PASS, exit 0                   | Ruff, Prettier, ESLint, Stylelint, TypeScript, probes   |
| Docker frontend build  | PASS, exit 0                   | Produkcyjny Next build                                  |
| Cały zestaw Playwright | 67 passed, 8 skipped, 0 failed | Końcowy build, 50.8 s                                   |
| Nowe testy 016         | 24 passed                      | Okresy, kwoty, konflikty, retry, pliki, role, geometria |
| Responsive             | PASS                           | 1440/1024/390 px, brak overflow strony, pola 46 px      |
| Git diff --check       | PASS                           | Własny zakres zmian                                     |

Obraz myhomebudget-frontend:bolt016, Id sha256:12bf90449298ce81652812005f96b703cc30ccc7bcc331705869bec7d40b6b79. Izolowany frontend myhomebudget-ui016-preview, localhost:3016. Końcowe sesje narzędzi: testy 20153, quality 11714, build 12156; wszystkie exit 0.

## Scenariusze

- 12 miesięcy jest nieaktywnych przed potwierdzeniem; wiele miesięcy można aktywować w dowolnej kolejności.
- Data otrzymania może być poza okresem, kwota nie jest wypełniana przez źródło.
- Pobieranie kolejnych stron źródeł obejmuje 51. pozycję.
- Niepewny POST ponawia identyczny klucz i dane; wadliwy 201 nie potwierdza zapisu.
- Jednoznaczne odrzucenie po retry rozstrzyga niepewność i zachowuje szkic.
- PATCH zachowuje szkic przy konflikcie i wymaga ręcznego scalania z bieżącą wersją.
- DELETE i przejścia okresu prezentują konflikt poza zamkniętym potwierdzeniem.
- Zapis źródła blokuje odejście, zachowuje szkic i nie dodaje przychodu.
- Timeout uploadu nie uruchamia retry; stary GET nie zastępuje świeżego sprawdzenia listy.
- Dodanie, prywatne pobranie i usunięcie pliku nie tworzą ponownie przychodu.
- Utrata roli blokuje zapis, utrata członkostwa usuwa kontekst nawet przy 403 okresu.
- Regresja rodziny, firmy, fokusu, logowania i błędu wylogowania przechodzi.

## Ograniczenia

UI korzysta z mockowanych odpowiedzi API; nie weryfikuje transakcji rzeczywistego backendu. Osiem istniejących testów live/acceptance pominięto przez warunki środowiskowe. Brak nowego pomiaru P95 i pełnego audytu WCAG.

Formalny Test oraz odbiór 017 pozostają do wykonania po checkpointcie Implement. Ten dokument nie jest test-walkthrough.md i nie zamyka bolta.

## Historia napraw

Pierwszy quality zatrzymał się przez nieprawidłowe montowanie zależności przez junction. Narzędzia zachowano, punkt montowania poprawiono i pełny skrypt powtórzono z PASS.

Testy wykryły regresję fokusu firmy i komunikatu błędu wylogowania oraz dwa zbyt szerokie selektory. Poprawiono kod i selektory; końcowy cały zestaw zakończył się bez błędów.
