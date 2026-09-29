---
artifact: design-system
status: accepted
scope: application-ui
source: product-requirements.md sections 51-53; accepted family-management design v3
created: 2026-09-11T19:04:54+02:00
updated: 2026-09-29
---

# System projektowy UI — Domowe Finanse

## Cel i kierunek

Wiążący standard całej aplikacji. Uzupełnia [wymagania produktu](product-requirements.md), nie zastępuje reguł domenowych, kryteriów story ani autoryzacji backendu.

Kierunek: **jasna przestrzeń domowa, granatowa nawigacja i zielone akcenty**. Zatwierdzony widok zarządzania rodziną v3 jest podstawą wizualną pozostałych ekranów. Poprzednia ciemna paleta z niebieskimi akcjami została zastąpiona wspólnym jasnym motywem. Nie utrzymywać oddzielnego motywu dla pojedynczego modułu.

Priorytet: **czytelność → funkcjonalność → hierarchia informacji → spójność → estetyka**. Efekt premium budują typografia, odstępy, subtelne obramowania i spokojne powierzchnie.

## Stosowanie standardu

Przed zmianą ekranu przeczytać aktywny bolt, właściwe story i ADR-y z [indeksu decyzji](decision-index.md). Zakres funkcjonalny wynika z story; nie dodawać pustych modułów ani CTA kolejnych MVP. Dla interakcji uwzględnić default, hover, focus-visible, disabled, loading, success i error tam, gdzie mają zastosowanie. W odbiorze podać dowody dla klawiatury, walidacji, statusów tekstowych i uprawnień API.

## Wspólne tokeny

Źródłem implementacji jest `frontend/app/globals.css`, sekcja `:root`. Ciemna nawigacja lokalnie korzysta z tokenów tekstu sidebaru. Nie kopiować palety do komponentów ani wprowadzać wyjątków kolorystycznych per moduł.

| Rola | Token | Wartość |
| --- | --- | --- |
| Tło aplikacji | `--color-background` | `#F5F6F2` |
| Nawigacja | `--color-sidebar` | `#07101D` |
| Powierzchnia karty, formularza i tabeli | `--color-surface` | `#FFFFFF` |
| Powierzchnia pomocnicza | `--color-surface-elevated` | `#F0F4F1` |
| Akcja główna | `--color-primary` | `#126B61` |
| Hover akcji i linku | `--color-primary-hover` | `#0C5149` |
| Miękkie wyróżnienie | `--color-primary-soft` | `#EDF6F2` |
| Fokus na jasnej powierzchni | `--color-focus` | `#126B61` |
| Sukces | `--color-success` | `#126B61` |
| Ostrzeżenie | `--color-warning` | `#865B14` |
| Błąd | `--color-danger` | `#B6374D` |
| Tekst główny | `--color-text-primary` | `#172536` |
| Tekst pomocniczy | `--color-text-secondary` | `#596879` |
| Obramowanie pola | `--color-border` | `#C8D2D6` |
| Podział powierzchni | `--color-divider` | `#E0E6E5` |
| Tekst nawigacji | `--color-sidebar-text` | `#F4F7FC` |
| Tekst pomocniczy nawigacji | `--color-sidebar-muted` | `#A7B4C8` |

Status i błąd zawsze mają etykietę tekstową; kolor nie jest jedynym nośnikiem znaczenia. Ikony statusów stosować jako uzupełnienie. Typ obiektu nie wyznacza koloru: kredyt nie jest automatycznie czerwony.

## Typografia i odstępy

- Jeden font: **Geist Variable**, dostarczany lokalnie przez `@fontsource-variable/geist`. Ikony: Lucide, z tekstem dla istotnych działań.
- Tekst bazowy 15 px, wysokość linii 1,6. Tytuł ekranu 28–40 px; na telefonie 26 px. Tytuł sekcji 20–28 px, etykiety 13 px, metadane 11–13 px.
- Skala odstępów oparta na 4 px: 8, 12, 16, 20, 24, 28, 32. Promień kart 16 px, pól i przycisków 8 px, nawigacji zakładek 14 px.
- Subtelny cień powierzchni: `0 6px 24px #19382D04`. Bez dominujących gradientów, glow i glassmorphism.
- Kwoty formatować konsekwentnie dla waluty gospodarstwa. Źródłem są wartości dziesiętne API; nie obliczać kwot przez float w UI. Nie utożsamiać kwoty umowy lub podpowiedzi miesięcznej z faktycznym przychodem.
- Kontrast tekstu i istotnych elementów interaktywnych sprawdzać w rzeczywistym zestawieniu kolorów zgodnie z WCAG 2.2 AA. Subtelne separatory nie zastępują etykiet ani widocznego fokusu.

## Shell i responsywność

Desktop: **Sidebar + Topbar + Main Content**. Sidebar ma 248 px, treść wspólną maksymalną szerokość 1800 px i odstęp 32 px. Nagłówek, wybór gospodarstwa i breadcrumbs są wspólne dla rodziny oraz ustawień. Formularz nowego gospodarstwa korzysta z tego samego shellu.

Przy szerokości do 900 px nawigacja przechodzi nad treść. Do 480 px nagłówek nawigacji i topbar są kompaktowe; breadcrumbs można ukryć, zachowując tytuł i wybór gospodarstwa. Nie ukrywać krytycznych działań. Karty osób przechodzą do jednej kolumny. Szerokie tabele mają własny, podpisany i dostępny klawiaturą obszar przewijania; nie rozszerzają całej strony.

Logowanie, pierwsze konto i przyjęcie zaproszenia korzystają z tej samej jasnej palety, białych paneli i zielonych przycisków. Nie wymagają sidebaru przed uwierzytelnieniem.

## Komponenty i wzorce ekranów

| Ekran / obiekt | Wzorzec |
| --- | --- |
| Członkowie rodziny | Karty: inicjały, imię, relacja, tekstowy status, konto, przypisane źródła, Edytuj. Jedno wspólne objaśnienie o koncie. |
| Źródła dochodu | Oddzielne dane osób i gospodarstwa, kompaktowe stany puste, biała tabela. |
| Umowy i firmy | Biała tabela, formularz otwierany na żądanie, słownik firm jako osobny widok; mały modal nowej firmy zachowuje dane umowy. |
| Ustawienia, dostępy, zaproszenia | Białe panele, wspólne pola, tabele i statusy; czytelna różnica między rolą konta a relacją rodzinną. |
| Tworzenie gospodarstwa | Jeden formularz i lokalne Anuluj, gdy użytkownik ma inne gospodarstwo. |
| Konto i przyjęcie zaproszenia | Skupiony formularz, wyraźny tytuł, wspólne komunikaty i akcje. |
| Przyszłe moduły finansowe | Ten sam shell i tokeny; tabele danych strukturalnych, analityczne wykresy i KPI stosownie do zadania. |

Zakładki modułu mają jedną aktywną sekcję, rzeczywiste liczniki, role tablist/tab/tabpanel i obsługę strzałek oraz Home/End. Nie prezentować wszystkich formularzy i słowników równocześnie.

Karta lub panel odpowiada za jeden temat. Dane porównywalne prezentować w tabelach, osoby w kartach. Nie zagnieżdżać dekoracyjnych paneli bez potrzeby. Wykresy proste: line, area, bar, horizontal bar lub donut; bez 3D i dekoracyjnych animacji.

## Formularze, działania i dostępność

- Akcja główna: zielone tło i biały tekst. Drugorzędna: białe tło, obramowanie i ciemny tekst. Niebezpieczna: czerwony tekst i obramowanie, jawne potwierdzenie oraz zachowanie semantyki historii.
- Pola mają widoczne etykiety, minimum 44 px wysokości i tekstowe błędy. Zachowywać niesekretne wartości po błędzie. Nie używać placeholdera zamiast etykiety.
- Wyraźny fokus 3 px; dostosować kolor do jasnej powierzchni lub ciemnej nawigacji. Całość dostępna klawiaturą. Akcje ikonowe mają nazwę dostępną; ważne akcje otrzymują tekst.
- Modal przenosi fokus do pierwszego pola, obsługuje Escape i przywraca fokus po zamknięciu. Ma lokalne Anuluj i nie gubi danych formularza nadrzędnego.
- Przyciski mają standardowo minimum 44 px; kompaktowe akcje i przyciski ikonowe minimum 32 px, preferowane 36–40 px. Drag and drop ma alternatywę przyciskową lub klawiaturową.
- Każdy widok uwzględnia ładowanie, brak danych, błąd i brak uprawnień. Komunikat wskazuje możliwy następny krok bez ujawniania szczegółów serwera ani danych obcego gospodarstwa.
- Copy jest po polsku, krótkie i funkcjonalne. Nie deklarować bezpieczeństwa lub szyfrowania bez potwierdzenia implementacji.

## Odbiór

Sprawdzić spójność tokenów we wszystkich zmienionych ekranach, desktop i telefon, focus i tabulację, Enter/Escape, etykiety, tekstowe statusy, lokalne przewijanie tabel i czytelność kwot. UI jedynie odzwierciedla uprawnienia backendu. Budżet jest planem, nie saldem. Ocena wizualna nie stanowi pełnego audytu WCAG.

Po zmianie kodu obowiązują formatter i lint z [coding-standards.md](coding-standards.md), `scripts/quality.ps1` oraz kontrola zmienionych widoków. Przed pierwszym modułem analityki wybrać bibliotekę wykresów i zapisać decyzję w ADR.
