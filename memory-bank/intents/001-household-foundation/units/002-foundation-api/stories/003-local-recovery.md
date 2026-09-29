---
id: 003-local-recovery
unit: 002-foundation-api
intent: 001-household-foundation
status: complete
priority: must
created: '2026-09-09T22:26:09.504Z'
assigned_bolt: 002-foundation-api
implemented: true
requirements:
  - FR-01
---
# Lokalne odzyskiwanie dostępu

## User Story
Jako operator instalacji chcę odzyskać dostęp do konta, aby korzystać z aplikacji po utracie hasła.

## Kryteria akceptacji
- [x] Operator z dostępem do lokalnej instalacji może według instrukcji zmienić hasło wskazanego użytkownika bez SMTP.
- [x] Zmiana hasła unieważnia wcześniejsze sesje; zwykły użytkownik bez uprawnień operatora nie ma dostępu do tego mechanizmu przez publiczny endpoint.
- [x] Nieistniejące konto nie powoduje utworzenia nowego konta ani zmiany ról; nowe hasło nie trafia do logów.

## Zależności
Bolty wymagane: 001-local-runtime.
W tym bolcie poprzedzają: 001-bootstrap-account, 002-session-login.
Pełna identyfikacja story: 002-foundation-api/003-local-recovery.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
