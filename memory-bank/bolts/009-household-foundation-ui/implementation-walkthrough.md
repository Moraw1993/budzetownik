---
stage: implement
bolt: 009-household-foundation-ui
status: accepted
created: 2026-09-23T07:53:54Z
---

# Raport implementacji: gęstość i responsywność ekranów gospodarstwa

## Wynik

Usunięto przyczynę dużych pustych obszarów: wspólny limit szerokości wszystkich formularzy zastąpiono wariantami dopasowanymi do zadania. Selektor gospodarstwa ma ograniczoną szerokość, edycja członków i relacji zajmuje sąsiednie kolumny na szerokim ekranie, a formularz dochodu wykorzystuje trzy kolumny pól. Po akceptacji uwagi projektowej „Dostępy” przeniesiono do ustawień aktywnego gospodarstwa, a ekran startowy pokazuje dane członków. Tabele zachowują szerokość paneli; dane, API i role nie uległy zmianie.

## Organizacja

Wspólny komponent panelu przyjmuje klasę układu. Komponenty ekranów wybierają wariant formularza, a reguły responsywne pozostają w istniejącym arkuszu stylów. Kolejność elementów w dokumencie pozostała zgodna z kolejnością czytania i obsługi klawiaturą.

## Zmienione pliki

- [x] `frontend/app/components/ui.tsx` — panel udostępnia klasę układu.
- [x] `frontend/app/components/household-shell.tsx` — selektor aktywnego gospodarstwa ma własną klasę kontekstu, formularz nowego gospodarstwa zachowuje zwarty wariant, a nawigacja oddziela dane od ustawień gospodarstwa.
- [x] `frontend/app/components/application.tsx` — ponowne sprawdzenie dostępu zachowuje wybraną sekcję, a wylogowanie przywraca startowy widok danych.
- [x] `frontend/app/components/access-panel.tsx` — formularz zaproszenia zachowuje zwarty wariant po usunięciu ogólnego limitu.
- [x] `frontend/app/components/members-panel.tsx` — tabela pozostaje szeroka, a formularz członka i zarządzanie relacjami tworzą jeden obszar edycji.
- [x] `frontend/app/components/income-panel.tsx` — formularz dochodu używa szerokiego wariantu panelu.
- [x] `frontend/app/globals.css` — jawne szerokości formularzy, siatki paneli, responsywna liczba kolumn i szerokości akcji, w tym przycisku zmiany roli.

## Decyzje

- **Warianty formularzy**: Proste formularze pozostają zwarte, a rozbudowany formularz dochodu korzysta z dostępnej szerokości bez wymuszania jej w pozostałych sekcjach.
- **Dwie kolumny edycji członków**: Formularz i relacje są bliskimi zadaniami; ich zestawienie usuwa pustą powierzchnię pod tabelą. Przy mniejszej szerokości układają się pionowo.
- **Pola dochodu**: Pola wyboru przypisania i opisu są szersze poza siatką pól szczegółowych. Zachowuje to ich naturalną kolejność oraz czytelność bez dodatkowych elementów formularza.
- **Przyciski**: Na desktopie główna akcja ma szerokość odpowiadającą treści, a na telefonie wypełnia dostępny wiersz.
- **Położenie dostępów**: Role i zaproszenia należą do wybranego gospodarstwa, więc znajdują się w jego ustawieniach, nie w osobistym koncie. Po wejściu i po zmianie gospodarstwa otwiera się widok członków.

## Odstępstwa od planu

Zamiast dodawać osobne spany dla przypisania i opisu, wykorzystano ich istniejące położenie poza siatką szczegółów i ograniczono maksymalną szerokość dla czytelności. Dodatkowo oznaczono formularz zaproszenia jako zwarty, aby zmiana wspólnej reguły nie rozszerzyła go przypadkowo. Na podstawie zaakceptowanej później uwagi projektowej rozszerzono zakres o przeniesienie „Dostępów” do ustawień gospodarstwa. Nie dodano zależności.

## Weryfikacja implementacji

- [x] Każdy zmieniony plik kodu sformatowano bezpośrednio po edycji; ESLint i Stylelint przeszły.
- [x] `scripts/quality.ps1` przeszedł, w tym Prettier, Ruff, ESLint, Stylelint i TypeScript.
- [x] Produkcyjny build Next.js i przebudowa frontendu w Compose przeszły.
- [x] Istniejące izolowane testy UI po zmianie nawigacji: 25 przeszło, 2 scenariusze live pominięte bez flagi środowiskowej.
- [x] W nagraniu testowym przy szerokości 1280 px sprawdzono selektor, dwie kolumny edycji członków i trzy kolumny formularza dochodu.
- [x] Przejrzano selektory i odpowiedzialności komponentów; nie znaleziono niezamierzonej duplikacji reguł układu.

Podgląd po zmianie: [członkowie i selektor](evidence/after-members-1280.jpeg), [formularz dochodu](evidence/after-income-1280.jpeg). To kadry kontrolne z nagrania testowego; pełne zrzuty trzech docelowych rozdzielczości powstaną w etapie testów.

## Pozostały etap

Użytkownik zaakceptował zmianę projektową i etap implementacji. Etap testów doda pomiary i zrzuty przy 1440×900, 1024×768 i 390×844, sprawdzi brak poziomego przepełnienia, obsługę klawiaturą i widoczny focus oraz ponowi właściwe testy funkcjonalne. Ten raport nie oznacza jeszcze spełnienia wszystkich kryteriów story.
