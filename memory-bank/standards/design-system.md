---
artifact: design-system
status: accepted
scope: application-ui
source: product-requirements.md sections 51-53
created: 2026-09-11T19:04:54+02:00
updated: 2026-09-11T19:04:54+02:00
---

# System projektowy UI — Domowe Finanse

## Cel i status

Ten dokument jest wiążącym standardem interfejsu dla aplikacji. Uzupełnia [wymagania produktu](product-requirements.md), nie zastępuje kryteriów story, reguł domenowych ani kontroli autoryzacji po stronie backendu.

Kierunek: **Future / Premium Financial Dashboard** — nowoczesny, spokojny i minimalistyczny. Wrażenie przyszłości budują głębia powierzchni, światło i oszczędne akcenty; nie cyberpunk, gaming ani nadmiar neonów.

Priorytet decyzji projektowej: **czytelność → funkcjonalność → hierarchia informacji → spójność → estetyka**.

## Adnotacje dla agenta `specs.md`

Przed zaplanowaniem lub zmianą ekranu agent:

1. Czyta aktywny `specs.md`/bolt, właściwy `unit-brief.md`, story i wymagania. Ustalenia konkretnego bolta mają pierwszeństwo w zakresie funkcji, ale nie mogą osłabić wymagań dostępności i niezmiennych zasad poniżej.
2. Czyta ten standard oraz właściwe ADR-y z `memory-bank/standards/decision-index.md`.
3. Projektuje tylko to, co obejmuje story. Nie dodaje pustych ekranów ani CTA dla MVP 2–5.
4. Dla każdej interakcji opisuje stan: domyślny, hover, `focus-visible`, disabled, loading, success i error — o ile stan ma zastosowanie.
5. W kryteriach odbioru zapisuje dowody: zachowanie klawiatury, walidację, tekstowy status oraz odpowiedź API tam, gdzie dotyczy uprawnień.

### Kontekst bieżącej implementacji

Początkowy ekran informujący o gotowości środowiska w `frontend/app/` używa zielonej palety i marketingowego copy. Jest ekranem bootstrapowym, a nie wzorcem docelowego systemu. Bolt, który pierwszy zmienia ten widok lub tworzy docelowy shell aplikacji, musi zastosować ten standard albo udokumentować świadome odstępstwo w ADR.

### Mapowanie na aktualny zakres UI

| Artefakt | Wymaganie dla implementacji |
| --- | --- |
| 003-household-foundation-ui / stories 001–003 | Formularze kont, gospodarstw i zaproszeń: funkcjonalne copy, czytelne komunikaty błędów, pełna obsługa klawiaturą. |
| 003-household-foundation-ui / stories 004–005 | Tabele lub listy członków i źródeł dochodu, stany puste, dostępne akcje edycji oraz jawne potwierdzenie dezaktywacji. |
| Przyszłe budżety, kredyty i oszczędności | Stosować model dashboardu, tabele i semantykę kolorów poniżej; nie włączać tych modułów do bolta fundamentu. |

## Fundament wizualny

### Kolory

| Rola | Token | Wartość | Zastosowanie |
| --- | --- | --- |
| Tło aplikacji | `--color-background` | `#08111F` | Główne tło; nie używać czystej czerni jako dominującego tła. |
| Sidebar | `--color-sidebar` | `#07101D` | Stała nawigacja desktopowa. |
| Powierzchnia | `--color-surface` | `#101C30` | Karty, formularze, tabele. |
| Powierzchnia podniesiona | `--color-surface-elevated` | `#132039` | Popover, modal, wyróżniona karta. |
| Akcja neutralna | `--color-primary` | `#4F8CFF` | Główna interakcja, aktywny wybór. |
| Sukces | `--color-success` | `#41D6A3` | Stan poprawny, zapłacony, wzrost. |
| Informacja pomocnicza | `--color-purple` | `#9B75FF` | Drugorzędne wyróżnienie, nie błąd. |
| Uwaga | `--color-warning` | `#E9B35C` | Stan wymagający uwagi. |
| Błąd | `--color-danger` | `#FF647C` | Błąd, zaległość, strata. |
| Tekst główny | `--color-text-primary` | `#F4F7FC` | Nagłówki i wartości. |
| Tekst drugorzędny | `--color-text-secondary` | `#A7B4C8` | Etykiety i opis. |
| Tekst pomocniczy | `--color-text-muted` | `#7788A1` | Metadane i pomoc. |

Kolor koduje znaczenie, nie typ obiektu: kredyt nie jest automatycznie czerwony. Status zawsze łączy **tekst + ikonę + kolor**, np. `✓ Zapłacona`, `○ Planowana`, `! Zaległa`.

### Typografia, wartości i spacing

- Preferowane kroje: Inter, Geist lub Manrope. Wybór techniczny należy ustalić raz dla aplikacji, nie per ekran.
- Hierarchia: nazwa widoku → główne wartości → nazwy sekcji → dane → informacje pomocnicze.
- Kwoty formatuje się konsekwentnie dla waluty gospodarstwa i wyrównuje w tabelach tak, aby były skanowalne; ich źródłem są wartości dziesiętne z API, nigdy obliczenia float w UI.
- Używać spójnej skali opartej na 4 px. Elementy nie powinny otrzymywać pojedynczych, przypadkowych odstępów.
- Kontrast tekstu, ikon i obramowań musi spełniać WCAG 2.2 AA w rzeczywistych kolorach komponentu.

### Layout i responsywność

Desktopowy shell ma układ **Sidebar + Topbar + Main Content**. Widoki zachowują wspólną szerokość treści, spacing, tytuł widoku i hierarchię.

- Breadcrumb jest widoczny w widokach hierarchicznych, np. `Budżet / 2026 / Wrzesień`.
- Dashboard zawiera zwykle 3–5 głównych KPI oraz 2–4 sekcje. Szczegóły prowadzą na kolejne poziomy.
- Ekran operacyjny (miesiąc budżetowy, harmonogram kredytu, edycja dochodów) eksponuje zadanie; wykresy i KPI nie mogą go zdominować.
- Projekt jest desktop-first, ale przy węższym widoku nie może ukrywać krytycznych akcji, danych ani alternatywy dla gestu.

## Komponenty i zachowanie

### Karty, dane i wykresy

- Standardowa karta odpowiada za jeden temat i najwyżej jedno główne CTA.
- Dla danych strukturalnych preferowane są tabele, szczególnie dla budżetu, harmonogramów, dochodów, inwestycji i historii operacji. Karty nie zastępują tabel wyłącznie dla estetyki.
- Wykresy są proste i analityczne: line, area, bar, horizontal bar albo donut. Bez 3D, wielu gauge, agresywnych gradientów i dekoracyjnych animacji.
- Subtelny glow, gradient, glassmorphism i głębia są akcentem użytym oszczędnie, nie warstwą na większości elementów.

### Formularze i akcje

- Proste wartości edytować inline lub w małym popoverze; duże modale rezerwować dla złożonych obiektów, operacji destrukcyjnych, zaawansowanej edycji i istotnych potwierdzeń.
- Każde pole ma widoczną etykietę. Błąd wyjaśnia co poprawić i zachowuje niesekretne dane wpisane przez użytkownika.
- Każda kontrolka interaktywna jest dostępna klawiaturą, ma wyraźny `focus-visible` i aktywny obszar co najmniej 32 × 32 px (dla przycisków ikonowych preferowane 36–40 px). Glow sam w sobie nie jest focusem.
- Drag and drop zawsze ma równoważną akcję klawiaturową lub przyciskową, np. „Przenieś wyżej”, „Przenieś niżej”, „Przenieś do grupy”.
- Akcja niszcząca wymaga jawnego potwierdzenia. Usunięcie/wyłączenie obiektu z historią nie może sugerować usunięcia historii, jeśli backend jej nie usuwa.

### Copy i stany

Copy jest funkcjonalne, po polsku i bez sloganów lub tekstów motywacyjnych. Preferowane przykłady: „Pozostało do rozdysponowania”, „Najbliższa rata”, „Postęp celu”, „Pozostało do spłaty”.

Każdy widok danych projektuje również stan ładowania, pusty, błąd i brak uprawnień. Komunikat ma wskazać następne możliwe działanie, ale nie ujawniać technicznych szczegółów serwera ani istnienia danych obcego gospodarstwa.

## Reguły niezmienne i odbiór

Przed zakończeniem bolta agent sprawdza:

- czy interfejs nie jest jedyną granicą uprawnień — UI jedynie odzwierciedla decyzję backendu;
- czy komunikaty finansowe nie mylą planu budżetu z saldem lub faktycznym wydatkiem;
- czy stan, status i błąd są zrozumiałe bez rozróżniania barw;
- czy kolejność tabulacji, focus, etykiety i obsługa Enter/Escape są sprawdzone w rzeczywistym widoku;
- czy tabelę można odczytać i obsłużyć na docelowej szerokości, a ważne kwoty i statusy nie są ucięte;
- czy efekt wizualny poprawia orientację. Jeżeli pogarsza czytelność lub zwiększa gęstość bez wartości użytkowej, należy go usunąć.

## Otwarte decyzje

- Zatwierdzić jeden krój pisma oraz sposób jego lokalnego dostarczania.
- Wybrać bibliotekę wykresów przed pierwszym modułem analityki; decyzję zapisać w ADR.
- Zdefiniować docelowe komponenty bazowe i nazwy tokenów w kodzie przed rozszerzeniem pierwszego ekranu poza bootstrap.
