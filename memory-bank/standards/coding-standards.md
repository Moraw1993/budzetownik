# Standardy jakości

## Źródło
Wymagania jakościowe z [product-requirements.md](product-requirements.md), sekcje 49–60, 63 i 67.
Formatowanie: Prettier i Ruff. Kontrola jakości: ESLint, Stylelint i Ruff. Testy backendu: Django TestCase oraz integracyjne testy runtime.

## Organizacja

Praca na branchach bolta/taska i commit po każdej większej zmianie są obowiązkowe zgodnie z [git-workflow.md](git-workflow.md).
Backend organizowany według domen modularnego monolitu z sekcji 56.
Reguły finansowe i autoryzacja egzekwowane w backendzie.
Nazwy encji zgodne ze słownikiem z sekcji 61. Użytkownik i członek gospodarstwa to odrębne pojęcia.

## Poprawność
Kwoty dziesiętne, operacje wieloetapowe transakcyjne, zmiany schematu przez migracje Django.
Budżet opisuje plan rozdysponowania, nie rzeczywiste wydatki ani saldo.
Przekroczenie przychodów wymaga wyraźnego ostrzeżenia.
Edycja zamkniętego miesiąca wymaga ponownego otwarcia.
Harmonogram bankowy oznaczony jako referencyjny ma pierwszeństwo przed obliczeniowym.

## Weryfikacja
Kryteria weryfikacji wywodzimy z reguł BR-01–BR-10 i wymagań poszczególnych modułów.
Należy weryfikować izolację gospodarstw i role po stronie backendu, integralność historii, obliczenia dziesiętne, wersjonowanie harmonogramów i brak podwójnego liczenia oszczędności.
PRD określa cel P95 < 500 ms dla podstawowych operacji API bez integracji zewnętrznych; dane i warunki pomiaru do zdefiniowania.
Dobór frameworków testowych i szczegółowej strategii pozostaje otwarty.

## Błędy i audyt
Walidacja danych i czytelne ostrzeżenia zgodnie z PRD.
Audyt istotnych zmian: wykonawca, czas, obiekt, wartość poprzednia i nowa.
Logowanie zdarzeń bezpieczeństwa wymagane; format błędów, narzędzia logowania i retencja do ustalenia.

## Obowiązkowe formatowanie po każdej zmianie kodu
Wymaganie użytkownika: każdy nowy lub edytowany plik musi być poprawnie sformatowany dla danego języka bezpośrednio po zmianie, przed kolejnym etapem i oddaniem pracy.
Python: Ruff format + Ruff check. TS/TSX/JS/JSON/YAML/CSS: Prettier; TS/JS: ESLint; CSS: Stylelint.
Źródłowy CSS nie może być minifikowany: osobna linia dla deklaracji, wielowierszowe bloki, puste linie między selektorami.
Wspólny kod współdzielić, wyszukiwać istniejące implementacje przed dodawaniem nowych. Usuwać niezamierzone powtórzenia funkcji, klas, komponentów, selektorów i właściwości.
Funkcje i klasy powinny mieć jedną odpowiedzialność; rozdzielać widoki HTTP, logikę domenową, prezentację i style. Formatter nie zastępuje przeglądu architektury ani wykrywania powielonej logiki.
Zbiorcze sprawdzenie: scripts/quality.ps1; poprawki formatowania: scripts/quality.ps1 -Fix. Nie formatować plików dystrybucji frameworka, zależności ani artefaktów wygenerowanych.
Przed zamknięciem bolta sprawdzić formatowanie, lint, duplikacje i testy. Nie wyłączać reguł w celu ukrycia problemu.
