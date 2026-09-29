# MyHomeBudget — zasady pracy

Przed implementacją przeczytaj memory-bank/standards/coding-standards.md oraz aktywny bolt specs.md.

## Git i AI-DLC

- Wydanie uruchamiaj wyłącznie po jawnej komendzie użytkownika `$realease_app`. Sama wzmianka o komendzie lub prośba o zapisanie tej reguły nie uruchamia wydania. Szczegóły określa standard pracy z Git.

- Przed zmianami stosuj [standard pracy z Git](memory-bank/standards/git-workflow.md). Obowiązuje we wszystkich fazach AI-DLC oraz zadaniach poza boltem.
- Nowe funkcje i zmiany wykonuj na branchu nazwanym według bolta lub taska, z aktualnego `develop`, nigdy bezpośrednio na `main` ani `develop`.
- Po każdej większej, spójnej i zweryfikowanej zmianie wykonaj commit przed rozpoczęciem kolejnego zakresu pracy oraz przed oddaniem etapu użytkownikowi.

- Przed merge do `develop` pobierz aktualne referencje, porównaj obie wersje, sprawdź konflikty i zweryfikuj połączone zmiany zgodnie ze standardem Git. Stabilne wydania trafiają z `develop` do `main` z tagiem `vMAJOR.MINOR.PATCH`.

## Obowiązkowo po utworzeniu lub edycji pliku kodu
- Uruchom właściwy formatter bezpośrednio po zmianie, a następnie sprawdź wynik.
- Python: Ruff format i Ruff check. TypeScript/TSX/JavaScript/JSON/YAML/CSS: Prettier; TS/JS dodatkowo ESLint, CSS dodatkowo Stylelint.
- Nie zapisuj minifikowanego CSS/JS jako kodu źródłowego. Każdy blok CSS jest wielowierszowy, deklaracje w osobnych wierszach, bloki oddzielone pustą linią.
- Funkcje, klasy i komponenty mają czytelne granice oraz jedną odpowiedzialność. Oddzielaj logikę domenową, obsługę HTTP, prezentację i style.
- Przed dodaniem funkcji, klasy, komponentu lub selektora wyszukaj istniejące odpowiedniki. Wspólną logikę współdziel, nie kopiuj. Nie twórz abstrakcji bez rzeczywistej potrzeby.
- Nie powielaj selektorów w tym samym kontekście CSS, właściwości, nazw funkcji i klas ani identycznej logiki. Celowe różnice w media queries są dozwolone.
- Formatowanie nie zastępuje przeglądu odpowiedzialności i duplikacji.
- Przed zakończeniem etapu uruchom scripts/quality.ps1, odpowiednie testy i sprawdź zmienione pliki.
- Nie wyłączaj reguł tylko po to, aby uzyskać zielony wynik.
- Nie formatuj bibliotek, plików wygenerowanych, zależności ani całej dystrybucji .specsmd.
