---
id: 001-compose-start
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
# Uruchomienie przez Compose

## User Story
Jako operator chcę uruchomić środowisko jedną komendą, aby korzystać z aplikacji lokalnie.

## Kryteria akceptacji
- [x] Na komputerze z Docker i konfiguracją według instrukcji, wykonanie docker compose up --build uruchamia frontend, Django i PostgreSQL oraz udostępnia lokalny adres aplikacji.
- [x] Gdy baza nie jest gotowa, usługi zgłaszają jednoznaczny stan i ponawiają połączenie; migracje mają określoną kolejność i nie uruchamiają się konkurencyjnie.
- [x] Porty aplikacji są wiązane z 127.0.0.1, PostgreSQL nie publikuje portu hosta; instrukcja opisuje lokalny HTTPS i zaufanie certyfikatu bez publicznego hostingu.

## Zależności
Bolty wymagane: Brak.
W tym bolcie poprzedzają: Brak.
Pełna identyfikacja story: 001-local-runtime/001-compose-start.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
