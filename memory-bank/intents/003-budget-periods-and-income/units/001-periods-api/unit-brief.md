---
unit: 001-periods-api
intent: 003-budget-periods-and-income
unit_type: backend
default_bolt_type: ddd-construction-bolt
phase: inception
status: complete
created: '2026-10-06T20:32:37Z'
updated: '2026-10-07T17:37:46Z'
---

# API okresów rozliczeniowych

## Cel i granica

Rozszerzyć modularny monolit Django o gospodarstwowe lata i miesiące rozliczeniowe. Jednostka jest właścicielem reguł kalendarza i przejść stanów okresu. Nie przechowuje wpisów przychodu.

## Wymagania przypisane

Właściciel reguł: FR-01, FR-02 i FR-07. Inne jednostki wywołują te operacje lub pokazują ich wynik; nie mogą omijać walidacji API.

## Zakres zachowania

- Rok gospodarstwa zawiera dokładnie 12 miesięcy kalendarzowych od stycznia do grudnia; duplikat roku jest odrzucany także przy współbieżnych żądaniach.
- Wszystkie miesiące rozpoczynają jako `inactive`; utworzenie roku nie aktywuje okresu.
- Uprawniony Owner lub Administrator jawnie aktywuje wybrany miesiąc. Aktywacja nie zależy od poprzedniego miesiąca; wiele miesięcy może być aktywnych równocześnie.
- Aktywny miesiąc można zamknąć. Zamknięty okres wymaga jawnego ponownego otwarcia przed modyfikacją wpisów. Okres nieaktywny nie przyjmuje wpisów.
- Member i Viewer odczytują zgodnie z istniejącą polityką, lecz nie zapisują ani nie zmieniają stanu.
- Zmiany stanu i wykonawca są audytowani według istniejących standardów.

## Interfejs i zależności

API udostępnia listę/tworzenie lat, odczyt miesięcy oraz jawne operacje aktywacji, zamknięcia i ponownego otwarcia. Dokładne ścieżki, format odpowiedzi, blokady współbieżności i nazwy stanów ustali projekt techniczny bolta 013. Zależy od istniejącego gospodarstwa, członkostwa, ról i audytu.

## Stories

Łącznie 3 stories Must; przypisane do bolta 013.

- [ ] **001-create-year-months** — Must — 013-periods-api
- [ ] **002-activate-month** — Must — 013-periods-api
- [ ] **003-close-and-reopen-month** — Must — 013-periods-api

## Bolt i kryteria zakończenia

Bolt 013-periods-api. Testy modelu/API obejmują granice lat, brak duplikatów, dokładnie 12 miesięcy, stany początkowe, równoległe/nieuporządkowane aktywacje, role, przejścia zamknięcia i audyt.

## Wyłączenia

Nie obejmuje rzeczywistych wpisów przychodu, wydatków, planu budżetu ani automatycznego aktywowania miesiąca.
