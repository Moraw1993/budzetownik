# Zarządzanie rodziną — projekt i kontrola v3

final result: passed

## Decyzja projektowa

Użytkownik zlecił nową koncepcję, prototyp, niezależną ocenę i wdrożenie po przekroczeniu 7,5/10. Osobny agent design_review ocenił wizualizację na **8,0/10**, a działające wdrożenie na **8,1/10**. Oba wyniki przekraczają wymagany próg.

Nowy kierunek: granatowa nawigacja aplikacji, jasne ciepłe tło, białe powierzchnie, zielona akcja główna. Członkowie są kartami z relacją, kontem i przypisanymi źródłami. Źródła oraz umowy pozostają oddzielnymi zakładkami z rzeczywistymi licznikami. Formularze i słowniki otwierają się na żądanie.

## Dowody wizualne

- Koncepcja: `.runtime/family-design-v3.png`.
- Desktop: `.runtime/ui-v3-desktop-members.jpg`, `.runtime/ui-v3-desktop-sources.jpg`, `.runtime/ui-v3-desktop-contracts.jpg`.
- Modal firmy: `.runtime/ui-company-dialog.jpg`.
- Mobile: `.runtime/ui-v3-mobile.jpg`, iframe o szerokości 390 px, obszar treści 375 px po uwzględnieniu paska przewijania.
- Koncepcję i wdrożenie obejrzano obok siebie na `/preview-comparison`, w równej szerokości i z zachowaniem proporcji. Nagłówek wdrożenia skrócono zgodnie z recenzją, powtarzane objaśnienia zastąpiono jednym, a przykładowe liczniki z makiety zastąpiono danymi API. Nie wdrożono niepotwierdzonych deklaracji szyfrowania ani nieczynnych menu z makiety.
- Błędne początkowe zrzuty fullPage odrzucono. Ocenę oparto na ponownie zapisanych zwykłych zrzutach, wizualnie sprawdzonych przed przekazaniem recenzentowi. Tymczasowe ustawienie viewportu przeglądarki zresetowano.

## Niezależna ocena wdrożenia

| Kryterium                | Waga | Ocena |
| ------------------------ | ---- | ----- |
| Wygoda obsługi           | 30%  | 8,0   |
| Hierarchia i organizacja | 25%  | 8,3   |
| Estetyka i efekt wow     | 20%  | 8,2   |
| Dostępność               | 15%  | 7,7   |
| Spójność i realizm       | 10%  | 8,5   |

Wynik ważony: 8,12/10, prezentowany jako **8,1/10**. Recenzent nie stwierdził widocznych problemów P0, P1 ani P2 na przedstawionych zrzutach. Drobne uwagi P3: dalsze skrócenie nagłówka mobilnego, wykorzystanie wolnego miejsca obok kart na bardzo szerokim ekranie i skrócenie opisu kwoty brutto w umowach.

## Kontrola interakcji

- Przełączenie trzech zakładek klawiszem Enter oraz nawigacja ArrowRight i Home: poprawne wybranie zakładki i przeniesienie fokusu.
- Formularz dodania umowy: fokus pierwszego pola; modal firmy: fokus nazwy firmy i dostępne lokalne Anuluj.
- Zapis firmy na danych demonstracyjnych: zamknięcie modalu, automatyczny wybór nowej firmy, zachowanie wpisanej nazwy umowy i powrót fokusu do pola Firma.
- Mobilna lista członków: jedna kolumna, wszystkie trzy zakładki widoczne.
- Mobilne źródła i umowy: szerokość dokumentu 375 px równa obszarowi treści; tabela przewijana we własnym kontenerze (349 px, zawartość 984 px), bez rozszerzenia całej strony.
- Konsola podglądu: brak błędów.

## Kontrola techniczna i granice

- Prettier, ESLint, Stylelint i produkcyjny build Next.js: przechodzą.
- `scripts/quality.ps1`: przechodzi po uzyskaniu dostępu do lokalnego Dockera; obejmuje Ruff, formatowanie, ESLint, Stylelint i TypeScript. Pierwsza próba w ograniczonym środowisku nie miała dostępu do Dockera.
- Podgląd korzysta wyłącznie z danych demonstracyjnych. Nie zmieniano prawdziwej bazy danych.
- Ocena wizualna nie stanowi pełnego audytu WCAG. Zapisy na rzeczywistym backendzie, wszystkie role i warianty archiwalne nie zostały objęte tą kontrolą. Pełny odbiór bolta 011 pozostaje osobnym etapem.

## Ujednolicenie aplikacji — 2026-09-29

Przyczyna niespójności: jasny motyw był ograniczony do klasy family-shell, podczas gdy ustawienia, tworzenie gospodarstwa i ekrany kont korzystały ze starych ciemnych tokenów. Przeniesiono paletę do :root, wspólne warianty do istniejących reguł komponentów i usunięto warunkowy motyw modułu. Ciemna nawigacja ma lokalne kolory tekstu oraz osobny, jasny fokus.

Przejrzane kroki:

1. Ustawienia i dostępy: spójne białe panele, zielone akcje, czytelne tabele; `.runtime/ui-settings.jpg`.
2. Nowe gospodarstwo: spójny shell i formularz, dostępne Anuluj; `.runtime/ui-create.jpg`.
3. Logowanie: jasna powierzchnia i wspólne pola/przyciski; `.runtime/ui-login.jpg`.
4. Pierwsze konto: ta sama hierarchia i czytelna pomoc hasła; `.runtime/ui-setup.jpg`.
5. Zaproszenie bez tokenu: czytelny czerwony komunikat i link powrotu; `.runtime/ui-invitation.jpg`.
6. Ustawienia mobilne: nawigacja kompaktowa; szerokość dokumentu 375 px równa viewportowi iframe, tabela przewijana lokalnie. Sprawdzono wizualnie w przeglądarce.

Zaktualizowano memory-bank/standards/design-system.md: wspólna paleta, Geist Variable, komponenty, responsywność, semantyka statusów, focus i mapa istniejących ekranów. Produkcyjny build oraz pełne scripts/quality.ps1 przechodzą. Przegląd był wizualny na danych demonstracyjnych; nie zapisywano ról, zaproszeń, haseł ani rzeczywistych danych. Nie jest to pełny audyt dostępności lub odbiór wszystkich przepływów backendu.
