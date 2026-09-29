# MyHomeBudget — zasady pracy

Przed implementacją przeczytaj memory-bank/standards/coding-standards.md oraz aktywny bolt specs.md.

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
