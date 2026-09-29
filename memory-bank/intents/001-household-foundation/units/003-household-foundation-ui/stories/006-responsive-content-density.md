---
id: 006-responsive-content-density
unit: 003-household-foundation-ui
intent: 001-household-foundation
status: complete
priority: must
created: '2026-09-23T07:22:20Z'
assigned_bolt: 009-household-foundation-ui
implemented: true
requirements:
  - FR-02
  - FR-06
  - FR-07
  - FR-08
---

# Responsywna gęstość ekranów gospodarstwa

## User Story

Jako osoba zarządzająca gospodarstwem chcę widzieć zwarte, dobrze wykorzystujące szerokość ekranu formularze i listy, aby szybciej przeglądać oraz edytować dane bez dużych pustych obszarów.

## Kryteria akceptacji

- [ ] Na szerokim ekranie selektor gospodarstwa ma czytelną, ograniczoną szerokość, a rola i waluta pozostają z nim w jednym logicznym wierszu.
- [ ] Lista członków wykorzystuje szerokość na dane, a formularz członka i zarządzanie relacjami tworzą zwarty układ dwóch kolumn, jeśli dostępne miejsce na to pozwala.
- [ ] Formularz źródła dochodu wykorzystuje responsywną siatkę: trzy kolumny na szerokim ekranie, mniej kolumn wraz ze zwężaniem widoku i jedną kolumnę na telefonie.
- [ ] Główne przyciski formularzy mają szerokość wynikającą z treści na desktopie i mogą zajmować pełną szerokość na małym ekranie.
- [ ] Przy szerokościach 1440 px, 1024 px i 390 px nie występuje poziome przewijanie całej strony, ucięcie treści ani utrata akcji; poziome przewijanie tabel pozostaje dostępne tam, gdzie jest potrzebne.
- [ ] Kolejność DOM, etykiety, widoczny focus, obsługa klawiatury i komunikaty formularzy pozostają poprawne po zmianie układu.

## Zależności

Bolty wymagane: 007-household-foundation-ui.
Pełna identyfikacja story: 003-household-foundation-ui/006-responsive-content-density.

## Uwagi techniczne

Zmiana dotyczy prezentacji istniejących ekranów. Nie zmienia API, modelu danych, ról ani reguł domenowych. Należy zastąpić ogólne ograniczenie szerokości bezpośrednich formularzy jawnymi wariantami układu oraz wykorzystać istniejące tokeny i skalę odstępów.
