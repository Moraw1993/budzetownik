# Dane i trwałość

## Źródło
[product-requirements.md](product-requirements.md), sekcje 35, 37, 49–50, 54–60, 63 i BR-01–BR-10.

## Baza danych
PostgreSQL jest źródłem prawdy dla danych aplikacyjnych.
Django ORM; każda zmiana schematu przez wbudowany system migracji Django.
Kwoty jako NUMERIC/DECIMAL, nigdy float; PRD podaje NUMERIC(18,2) jako przykład. Precyzja stóp procentowych i zasady zaokrągleń wymagają doprecyzowania.
Waluta od początku w modelu, domyślnie PLN; automatyczne przeliczanie walut poza początkowym zakresem.

## Integralność
Każdy obiekt finansowy należy do jednego gospodarstwa. Backend weryfikuje dostęp, również do obiektów powiązanych.
Operacje wieloetapowe, np. nadpłata i nowa wersja harmonogramu, są transakcyjne.
Saldo wynika z historii transakcji; korekta tworzy ADJUSTMENT.
Cele stanowią wirtualną alokację, bez podwójnego liczenia środków.
Zachowujemy wersje harmonogramów, historię miesięcy i audyt istotnych operacji.
Archiwizacja lub soft delete zamiast utraty historii.

## Dokumenty i kopie
Metadane załączników w PostgreSQL, pliki MVP w filesystemie na trwałym wolumenie Docker. PostgreSQL korzysta z osobnego trwałego wolumenu. Restart lub odtworzenie kontenerów zachowuje dane i załączniki; wolumeny nie zastępują kopii zapasowych. Object storage pozostaje możliwością przyszłej rozbudowy.
Wymagane regularne kopie zapasowe; harmonogram, retencja i procedura odtwarzania do ustalenia.
