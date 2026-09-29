---
id: 002-backup-restore
unit: 004-local-acceptance
intent: 001-household-foundation
status: complete
priority: must
created: '2026-09-09T22:26:09.504Z'
assigned_bolt: 008-local-acceptance
implemented: true
requirements:
  - NFR-02
---
# Kopia i odtworzenie danych

## User Story
Jako operator chcę odtworzyć instalację z kopii, aby odzyskać dane po awarii.

## Kryteria akceptacji
- [ ] Instrukcja opisuje kopię PostgreSQL, wolumenu załączników oraz wymaganej konfiguracji, bez ujawniania sekretów w repozytorium.
- [ ] Kopię odtworzono w odrębnej instalacji testowej; porównano gospodarstwa, członkostwa, źródła, audyt i kontrolny plik załącznika.
- [ ] Restart i odtworzenie kontenerów zachowują dane; instrukcja ostrzega przy poleceniach usuwających wolumeny i opisuje procedurę odzyskania konta.

## Zależności
Bolty wymagane: 009-household-foundation-ui.
W tym bolcie poprzedzają: 001-end-to-end-acceptance.
Pełna identyfikacja story: 004-local-acceptance/002-backup-restore.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
