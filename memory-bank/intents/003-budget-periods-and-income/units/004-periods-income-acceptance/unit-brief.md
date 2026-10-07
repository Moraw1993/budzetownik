---
unit: 004-periods-income-acceptance
intent: 003-budget-periods-and-income
unit_type: infrastructure
default_bolt_type: simple-construction-bolt
phase: inception
status: draft
created: '2026-10-06T20:32:37Z'
updated: '2026-10-06T20:32:37Z'
---

# Odbiór okresów i przychodów

## Cel i granica

Zweryfikować zintegrowany przepływ przez przeglądarkę i API na danych syntetycznych. Jednostka nie implementuje reguł domeny ani nie zmienia ich właścicieli.

## Zakres

- Utworzenie roku z dokładnie 12 nieaktywnymi miesiącami, niezależna aktywacja w dowolnej kolejności, zamknięcie/otwarcie oraz brak zapisu przy zamknięciu.
- Zachowanie ról Owner/Administrator wobec Member/Viewer i izolacji gospodarstw.
- Zapis wielu rzeczywistych przychodów dla osoby i gospodarstwa ze słownikowymi źródłami, datą wypłaty poza miesiącem, kwotami różnych walut oraz podsumowaniem per waluta.
- Dodanie wielu dopuszczonych załączników, odmowa niedozwolonego typu/rozmiaru i kontrola autoryzowanego pobrania.
- Zachowanie wpisów po restarcie aplikacji w środowisku odbioru.
- Pomiar P95 obejmuje jawnie endpointy lat/miesięcy i lifecycle z 013 oraz endpointy przychodów/sum; raport podaje fixture, warm-up, liczbę prób, współbieżność, percentyl i środowisko. Cel okresów <500 ms pozostaje niespełniony do czasu pomiaru lub jawnie zgłoszonej blokady.

## Zależności

Wymaga ukończenia 001-periods-api, 002-monthly-income-api, 003-periods-income-ui i istniejących usług gospodarstwa/źródeł. Scenariusze korzystają z syntetycznych kont i plików, nie z danych produkcyjnych.

## Stories

Łącznie 2 stories Must; obie w planowanym bolcie 017.

- [ ] **001-period-role-lifecycle** — Must — 017-periods-income-acceptance
- [ ] **002-income-journey-attachments** — Must — 017-periods-income-acceptance

## Kryteria zakończenia

Powtarzalne testy akceptacyjne sprawdzają pełne kryteria stories i raportują wynik dla każdej roli oraz tenant-a. Testy nie zależą od zewnętrznego banku, OCR ani publicznego magazynu plików.
