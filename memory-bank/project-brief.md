# Kontekst produktu i plan AI-DLC

Źródło nadrzędne wymagań: [product-requirements.md](standards/product-requirements.md).
Nazwa: Domowe Finanse / Household Finance Manager. Folder projektu: MyHomeBudget.
Stan: inicjalizacja na podstawie PRD; brak rozpoczętej implementacji i zaplanowanych boltów.

## Cel
Zastąpić arkusze Excel aplikacją do planowania budżetu, ewidencji kredytów, oszczędności i analityki gospodarstwa.

## Kolejność MVP według sekcji 64
1. Fundament: logowanie, gospodarstwa, członkowie, dochody, role.
2. Budżet: lata, miesiące, przychody, hierarchia, alokacje, kopiowanie i historia.
3. Kredyty: harmonogramy, raty, płatności, nadpłaty i dokumenty.
4. Oszczędności: rachunki, transakcje, korekty, cele.
5. Analityka: dashboard i wskaźniki budżetu, kredytów, oszczędności.

V2: inwestycje. V3: rzeczywiste wydatki. V4: synchronizacja bankowa. V5: prognozy i symulacje.
Nie realizujemy przelewów, transakcji giełdowych ani księgowości.

## Materiały źródłowe
- [rozdysponowanie-budzetu.xlsx](source-materials/rozdysponowanie-budzetu.xlsx) — obecny proces planowania.
- [splaty-kredytu.xlsx](source-materials/splaty-kredytu.xlsx) — kredyty; zakładka VeloBank dotycząca przelewów — oszczędności.
Arkusze nie zostały jeszcze przeanalizowane; ten opis ich roli pochodzi z PRD.

## Następny etap
Inception dla MVP 1: doprecyzowanie wymagań, kryteria akceptacji, podział na jednostki i plan boltów.

## Uzgodnione środowisko MVP
Lokalnie na komputerze użytkownika, przez Docker Compose; dostęp przez localhost. Backend Django, PostgreSQL oraz frontend w kontenerach. Baza i załączniki na trwałych wolumenach.
