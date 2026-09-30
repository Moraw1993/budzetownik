---
commit: d67098520692d0bea5b661db66408ddc5cd29e98
built: 2026-09-30T08:10:34Z
status: success
---

# Lokalny build kandydata d670985

Zakres: API i UI intentu 002, odbiór jednostki 003. Bez release, tagu Git i publikacji registry. Compose użył cache tych samych warstw i konfiguracji Python 3.13/Django oraz Node 22/Next.js co dev; indeksy obrazów zmieniają się przez metadane attestacji kolejnych buildów.

- Backend `myhomebudget-backend:local`: `sha256:a6d056105804063e070719f99e3c6dfbd16828eea096eb589c802354635b1ea7`.
- Frontend `myhomebudget-acceptance-17d4acaa-target-frontend:latest`: `sha256:706851a34cdcd42f37e794a02d1d8bf639debf11585c4c122d71864dc8163982`.

Build przeszedł. Quality i ponowne 83 testy backendu podczas odbioru dev opisuje [raport domknięcia](../../../../../operations/post-bolt-012.md).
