# Decyzje do doprecyzowania

PRD określa kierunek, ale nie rozstrzyga poniższych kwestii. Nie są to dodatkowe wymagania.

## Przed realizacją fundamentu
- Obsługa lokalnego HTTPS i certyfikatu zgodnie z wymaganiem PRD. Środowisko jest ustalone: lokalny Docker Compose na komputerze użytkownika.
- Finalny wariant frontendu: preferowany Next.js lub alternatywa React + Vite.
- Techniczna realizacja logowania i sesji oraz odzyskiwania dostępu. Uzgodniono: pierwsze konto podczas konfiguracji, kolejne przez kopiowane linki zaproszeń, bez e-maili.
- Rozstrzygnięto: Owner zarządza rolami i zaproszeniami; linki 7 dni, jednorazowe, odwoływalne; ochrona ostatniego Owner. Member/Viewer tylko odczyt, Owner/Administrator edytują członków i źródła. Szczegół modelu do przeglądu: intents/001-household-foundation/review.md.
- Menedżery pakietów, wersje, formatowanie, lintowanie i frameworki testowe.

## Przed kolejnymi modułami
- Precyzja, zaokrąglenia, naliczanie odsetek i daty harmonogramów.
- Tożsamość pozycji budżetu między miesiącami oraz przekształcanie kategorii w kategorię z elementami.
- Rozliczanie wpłat na cele i wypłat z rachunku finansującego wiele celów.
- Sposób prezentacji sum wielowalutowych bez automatycznych kursów.
- Wybór biblioteki wykresów, zakres migracji danych Excel i kryteria zgodności z arkuszami.
- Limity załączników, retencja audytu, kopie zapasowe i test odtworzenia.
- Dane testowe i warunki pomiaru celu P95 < 500 ms.
