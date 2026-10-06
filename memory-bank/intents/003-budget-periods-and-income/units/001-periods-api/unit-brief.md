---
unit: 001-periods-api
intent: 003-budget-periods-and-income
unit_type: backend
default_bolt_type: ddd-construction-bolt
phase: inception
status: draft
created: '2026-10-06T20:32:37Z'
updated: '2026-10-06T20:32:37Z'
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

Do utworzenia w jednostce: 001-create-year-months, 002-activate-month, 003-close-and-reopen-month.

## Bolt i kryteria zakończenia

Bolt 013-periods-api. Testy modelu/API obejmują granice lat, brak duplikatów, dokładnie 12 miesięcy, stany początkowe, równoległe/nieuporządkowane aktywacje, role, przejścia zamknięcia i audyt.

## Wyłączenia

Nie obejmuje rzeczywistych wpisów przychodu, wydatków, planu budżetu ani automatycznego aktywowania miesiąca.
