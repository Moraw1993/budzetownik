---
stage: implement
bolt: 006-household-foundation-ui
created: 2026-09-20T18:47:00Z
status: accepted
---

# Implementacja kont, gospodarstw i zaproszeń

## Podsumowanie

Zastąpiono ekran startowy interfejsem konfiguracji konta, logowania, gospodarstw, ról i zaproszeń. Interfejs używa rzeczywistych ścieżek istniejącego API oraz granatowego systemu wizualnego. Nie zmieniano modeli, reguł backendu ani danych użytkownika.

## Struktura i wykonane prace

- [x] frontend/app/lib/api.ts — kontrakty odpowiedzi, klient HTTP, świeży CSRF przed zapisem, limity czasu, anulowanie odczytów i bezpieczne błędy.
- [x] frontend/app/components/application.tsx — sesja, wybór kontekstu, przywracanie strony z historii i odbiór zaproszenia.
- [x] frontend/app/components/account-panel.tsx — konfiguracja, logowanie oraz przyjęcie zaproszenia przez istniejące lub nowe konto.
- [x] frontend/app/components/household-shell.tsx — sidebar, topbar, tworzenie gospodarstwa i przełączanie kontekstu.
- [x] frontend/app/components/access-panel.tsx — odczyt dostępów, zmiany ról Ownera, tworzenie, kopiowanie i odwoływanie zaproszeń.
- [x] frontend/app/components/ui.tsx — współdzielone kontrolki, formularz z blokadą wielokrotnego zapisu, walidacja pól i focus błędu; kompozycja przycisku według wzorca shadcn z Radix Slot.
- [x] frontend/app/page.tsx i frontend/app/accept-invitation/page.tsx — publiczne punkty wejścia interfejsu.
- [x] frontend/app/globals.css — tokeny, czytelne formularze i tabele, stany interakcji oraz responsywność. Usunięto nieużywany bootstrapowy page.module.css.
- [x] frontend/postcss.config.mjs, package.json i package-lock.json — Tailwind, Radix, Lucide, lokalny Geist Variable i narzędzia testów UI.
- [x] frontend/tests/foundation.spec.ts i playwright.config.ts — powtarzalne sprawdzenie interfejsu z kontrolowanym API w przeglądarce Edge na Windows; domyślny Chromium na innych systemach.

## Decyzje i ochrona kontekstu

- Konta korzystają z prefiksu /api/auth/, zweryfikowanego w backend/config/urls.py. Nie dodano alternatywnego API.
- Token zaproszenia znika z fragmentu adresu po odczycie i pozostaje tylko w pamięci. Nie zapisuje się go w localStorage. Po przyjęciu adres zmienia się na stronę główną.
- Wynik przyjęcia jest wiązany z membership_id z listy gospodarstw. Nie jest interpretowany jako identyfikator gospodarstwa.
- Zmiana kontekstu odmontowuje poprzedni panel; odczyty są anulowane, a późne mutacje nie przełączają użytkownika z powrotem do poprzedniego gospodarstwa.
- Przywrócenie strony i powrót do karty ponownie weryfikują sesję. Chroniona część widoku jest ukrywana przed zapisaniem migawki historii. Zachowywany jest wybrany kontekst, jeśli użytkownik nadal ma dostęp.
- Formularze zachowują niesekretne pola po walidacji i czyszczą hasło. Błędy 5xx nie wyświetlają treści odpowiedzi. Odmowa mutacji odświeża stan dostępu.
- Tabela ma poziome przewijanie, etykietę regionu, focus i obsługę strzałek. Na telefonie nie rozpycha całej strony i nie łamie krótkich nazw ról na pojedyncze litery.
- Font Geist Variable jest dostarczany lokalnie z paczki; przeglądarka nie pobiera fontów z zewnętrznego CDN.

## Weryfikacja implementacyjna

- 17/17 testów przeglądarkowych przeszło. Obejmują: walidację konta, błędne logowanie, wylogowanie i historię, role Administrator/Member/Viewer, ochronę ostatniego Ownera i odświeżenie odmowy API, tworzenie gospodarstwa, wyścigi odczytu i zapisu, zaproszenia dla obu typów kont, nieprawidłowy link, kopiowanie awaryjne, potwierdzenie odwołania, bezpieczne błędy serwera i wygaśnięcie sesji.
- Po ostatnim doprecyzowaniu mobilnej tabeli powtórzono jej test: 1/1, w tym focus regionu i przewijanie klawiszem ArrowRight.
- Testy przechwytują API w przeglądarce. Potwierdzają zachowanie UI, nie stanowią testu autoryzacji Django, bazy PostgreSQL, HTTPS ani rzeczywistego CSRF. Kontrolowany serwer testowy sprawdza obecność nagłówka CSRF w zapisach.
- Build produkcyjny Next.js: wynik pozytywny. TypeScript, Prettier, ESLint i Stylelint: wynik pozytywny, bez wyłączenia reguł.
- Ruff format --check i Ruff check: 51 plików, wynik pozytywny; backend nie był modyfikowany.
- Obejrzano zrzuty przy 1440 px i 390 px. Dowody lokalne: .runtime/bolt006-desktop.png i .runtime/bolt006-mobile.png. Dane w zrzutach są syntetyczne.
- scripts/quality.ps1 uruchomiono, ale przerwał pracę przy połączeniu z Dockerem. Także sprawdzenie poza sandboxem nie znalazło działającego demona. Próba uruchomienia Docker Desktop w tle nie udostępniła silnika.

## Odstępstwa i ograniczenia

Ograniczenia opisane podczas pierwszego przebiegu zostały usunięte 2026-09-21: uruchomiono scripts/quality.ps1, 68 testów Django, test trwałości oraz pełny scenariusz UI przez rzeczywiste HTTPS, API i PostgreSQL. Wyniki znajdują się w [raporcie testów](test-walkthrough.md).

W repozytorium nie ma metadanych Git, dlatego przegląd wykonano na zmienionych plikach i kontrolach statycznych. Sprawdzono rozdzielenie HTTP, sesji, formularzy, ekranów i stylów oraz brak powielonych selektorów. Bolt pozostaje in-progress/current_stage: test do czasu zatwierdzenia raportu testów.

## Uruchomienie kontroli

W katalogu frontend: npm ci, npm run test:ui, npm run build, npm run format:check, npm run lint, npm run lint:css i npm run typecheck. Testy izolowane otwierają uruchomioną aplikację na https://localhost:8443 i przechwytują odpowiedzi API; nie modyfikują danych lokalnej aplikacji. Na systemach innych niż Windows należy wcześniej zainstalować przeglądarkę Chromium dla Playwright.

Etap implementacji zatwierdzono poleceniem użytkownika „Kontynuuj pracę projektowo-implementacyjne zgodnie z specs.md”. Pełny przebieg wykonano po uruchomieniu Dockera; dalsze wyniki opisuje test-walkthrough.md.
