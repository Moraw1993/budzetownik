---
id: 001-migration-and-isolation
unit: 003-family-income-acceptance
intent: 002-family-income-management
status: complete
priority: must
created: '2026-09-23T08:26:40Z'
assigned_bolt: 012-family-income-acceptance
implemented: true
requirements:
  - FR-06
  - FR-07
---

# Odbiór migracji i izolacji gospodarstw

## User Story

Jako Owner chcę mieć pewność, że aktualizacja zachowa stare źródła i nie ujawni danych innego gospodarstwa.

## Kryteria akceptacji

- [ ] Na kopii danych testowych utworzonej na starym schemacie migracja zachowuje źródła, ich UUID, kwoty, powiązania, status i audyt.
- [ ] Stare „Wynagrodzenie” pozostaje innym źródłem do jawnego przekształcenia; liczba miesięcznych przychodów pozostaje zero.
- [ ] API odrzuca dostęp i powiązania z obcym gospodarstwem oraz próby zapisu Member/Viewer bez zmiany stanu i audytu.
- [ ] Restart lokalnych usług bez usunięcia wolumenów zachowuje firmy, umowy i źródła.

## Zależności

Bolty 010 i 011; syntetyczna kopia danych testowych.
