---
id: 002-persistent-storage
unit: 001-local-runtime
intent: 001-household-foundation
status: complete
priority: must
created: '2026-09-09T22:26:09.504Z'
assigned_bolt: 001-local-runtime
implemented: true
requirements:
  - NFR-02
---
# Trwałe dane i konfiguracja

## User Story
Jako operator chcę oddzielić dane od kontenerów, aby zachować dane po aktualizacji.

## Kryteria akceptacji
- [x] Gdy w bazie i wolumenie plików zapisano dane testowe, odtworzenie kontenerów bez kasowania wolumenów zachowuje ich zawartość.
- [x] Gdy brakuje wymaganej konfiguracji, start zgłasza błąd bez wypisywania sekretów; przykład konfiguracji nie zawiera rzeczywistych haseł.
- [x] Przy ponownym uruchomieniu istniejącej instalacji migracje nie usuwają danych i nie ponawiają konfiguracji pierwszego konta.

## Zależności
Bolty wymagane: Brak.
W tym bolcie poprzedzają: 001-compose-start.
Pełna identyfikacja story: 001-local-runtime/002-persistent-storage.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
