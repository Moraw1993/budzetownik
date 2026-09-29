# Standard pracy z Git w AI-DLC

## Zakres

Reguły obowiązują każdy model i agenta we wszystkich fazach AI-DLC: Inception, Construction i Operations, a także przy zadaniach poza boltem, zmianach dokumentacji i konfiguracji.

## Branch przed zmianami

1. Sprawdź aktualny branch, stan katalogu roboczego i istniejące branche. Zachowaj zastane zmiany użytkownika; nie nadpisuj ich, nie resetuj i nie dodawaj do własnego commita.
2. Przed pierwszą edycją utwórz lub wybierz branch odpowiadający bieżącemu boltowi albo taskowi. Przy kontynuacji użyj istniejącego brancha tego zakresu. Nowy branch wyprowadź z aktualnego `main`, chyba że zadanie zależy od pracy na innym branchu; wtedy użyj i odnotuj tę bazę.
3. Stosuj schemat `<typ>/bolt-<pełne-id-bolta>` albo `<typ>/task-<id-lub-opis-zadania>`. Typy: `feat` dla nowych funkcji, `fix` dla poprawek, `refactor` dla przebudowy, `docs` dla dokumentacji, `chore` dla narzędzi, konfiguracji i zasad pracy. Nazwy pisz małymi literami, bez spacji i polskich znaków, w kebab-case.
4. Przykłady: `feat/bolt-011-family-management-ui`, `fix/bolt-011-family-management-ui`, `chore/task-ai-dlc-git-workflow`.
5. Nie implementuj zmian bezpośrednio na `main`. Nie łącz niezależnych boltów lub tasków na jednym branchu. Przy zależnościach utwórz osobny branch z właściwej bazy.

## Commit po większej zmianie

Większa zmiana to ukończony, spójny fragment funkcji, poprawka błędu, refaktoryzacja, zmiana konfiguracji lub zestaw dokumentacji możliwy do osobnego przeglądu. Zakończenie etapu bolta również wymaga commita, jeśli powstały zmiany. Nie odkładaj wszystkich commitów do końca bolta i nie commituj każdej pojedynczej edycji.

1. Po takim fragmencie wykonaj wymagane formatowanie, lint i odpowiednie testy zgodnie z `coding-standards.md`. Przed zakończeniem etapu uruchom `scripts/quality.ps1`. Dla samych reguł i dokumentacji sprawdź spójność instrukcji, odnośniki i diff; testy aplikacji nie zastępują tego przeglądu.
2. Sprawdź diff i wybierz do indeksu wyłącznie pliki lub fragmenty należące do bieżącej zmiany. Nie dodawaj sekretów, prywatnych danych, zależności ani wygenerowanych artefaktów.
3. Wykonaj commit przed kolejnym większym zakresem pracy, przejściem do następnego etapu lub przekazaniem wyników użytkownikowi. To stały obowiązek, niewymagający ponownego pytania o zgodę na lokalny commit.
4. Używaj komunikatu `<typ>(<bolt-id-lub-task>): <konkretny opis>`, np. `feat(011-family-management-ui): add contract form` lub `chore(task-ai-dlc-git-workflow): define branch and commit rules`.
5. Jeśli wymagane sprawdzenia nie przechodzą, napraw błąd przed zamknięciem etapu. Jeśli commit blokuje środowisko lub uprawnienia, zachowaj zmiany i zgłoś konkretną blokadę; nie deklaruj commita ani zakończenia, które nie nastąpiły.
6. Po commicie sprawdź jego zakres i stan katalogu roboczego. W podsumowaniu podaj branch, hash commita i wynik weryfikacji. Zastane zmiany użytkownika mogą pozostać poza commitem.

## Publikacja i integracja

Commit lokalny, push i merge są osobnymi operacjami. Push wykonuj w ramach autoryzacji użytkownika dla bieżącego zadania. Nie wykonuj automatycznego merge do `main`, force push ani przepisywania istniejących commitów bez odpowiedniej autoryzacji.
