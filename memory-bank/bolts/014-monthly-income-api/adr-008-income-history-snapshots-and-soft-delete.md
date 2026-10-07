---
bolt: 014-monthly-income-api
created: 2026-10-07T12:16:28Z
status: accepted
superseded_by: null
---

# ADR-008: Snapshoty historii przychodu i miękkie usuwanie

## Context

Przychód jest historycznym faktem przypisanym do konkretnego odbiorcy i źródła. Nazwy członków, etykiety źródeł, firmy i rodzaje umów mogą zostać później zmienione, zarchiwizowane lub przekształcone. Sama referencja do aktualnego rekordu słownika nie wystarcza do wiernego wyświetlenia historii. Fizyczne usunięcie przychodu odłączyłoby również jego audyt i wynik idempotentnego utworzenia.

## Decision

`IncomeRecord` przechowuje bieżące identyfikatory gospodarstwa, okresu, odbiorcy i źródła jako klucze obce oraz osobne `recipient_snapshot` i `source_snapshot` przeznaczone do historycznego odczytu. Snapshot odbiorcy zachowuje rodzaj i etykietę osoby albo gospodarstwa. Snapshot źródła zachowuje identyfikator, nazwę, rodzaj, wersję słownika oraz — dla umowy — identyfikator i nazwę firmy oraz rodzaj umowy. Dla źródeł innych niż umowa część `contract` ma wartość `null`. Snapshoty nie kopiują kwot brutto, domyślnych kwot źródła ani innych obliczeń.

Zmiana kwoty, waluty lub daty otrzymania nie zmienia snapshotów. Przy przypisaniu do innego odbiorcy lub źródła walidujemy nową parę relacji i odświeżamy tylko snapshot relacji, której identyfikator rzeczywiście się zmienił. Przypisanie i zmiana snapshotu są audytowane zgodnie z ADR-004. Niezmienione, historyczne relacje pozostają widoczne nawet po późniejszej archiwizacji lub zmianie danych słownika.

Usunięcie przez API jest miękkie: ustawia `deleted_at` i `deleted_by`, zachowując relacje, snapshoty i audyt. Zwykłe listy, odczyt szczegółu, zmiany oraz sumy pomijają usunięte rekordy. Klucze obce chroniące historię używają `PROTECT`; trwałe usunięcie danych nie jest częścią tego API.

## Rationale

Snapshot oddziela historyczne znaczenie zapisanego przychodu od aktualnego stanu słownika, a klucz obcy nadal umożliwia autoryzowane zapytania i filtrowanie po tożsamości. Miękkie usunięcie zachowuje ślad finansowy i integralność audytu bez pokazywania wpisu w zwykłych widokach operacyjnych. Jawne odświeżanie snapshotów tylko przy zmianie relacji odróżnia korektę przypisania od zwykłej edycji wartości.

### Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
| --- | --- | --- | --- |
| Odczytywać historię wyłącznie przez bieżące rekordy słownika | Mniej danych w `IncomeRecord` | Archiwizacja, zmiana nazwy lub konwersja słownika zmienia historyczny widok | Historia musi zachować wartości z chwili zapisu |
| Kopiować dane słownika do snapshotu bez kluczy obcych | Snapshot pozostaje samowystarczalny | Utrudnia zapytania po tożsamości, tenant-scoping i walidację przyszłych przypisań | Potrzebne są jednocześnie referencje i wartości historyczne |
| Fizycznie usuwać przychód i kaskadowo usuwać powiązane dane | Prostsze usuwanie danych z tabel | Niszczy historię, audyt i powiązanie z wynikiem retry | API zachowuje rekord i oznacza go jako usunięty |
| Przy każdej edycji odświeżać wszystkie snapshoty | Etykiety zawsze odpowiadają aktualnemu słownikowi | Edycja kwoty mogłaby po cichu przepisać kontekst historyczny | Snapshot zmienia się tylko wraz z jawnie zmienioną relacją |

## Consequences

### Positive

- Historia zachowuje czytelne etykiety mimo zmian i archiwizacji słownika.
- Referencje domenowe pozostają dostępne do autoryzacji, zapytań i przypisań.
- Usunięcie nie usuwa śladu audytu ani klucza idempotencji.

### Negative

- Model i odpowiedź API zawierają dodatkowe pola JSON, których kształt wymaga ewolucji kontraktu.
- Soft-delete wymaga jawnego filtrowania usuniętych rekordów w listach, szczegółach i agregatach.

### Risks

- Snapshot może przypadkowo utrwalić dane wrażliwe lub zbędne. Whitelista ogranicza go do identyfikatorów, etykiet oraz rodzajów relacji; nie zawiera kwot źródła, załączników ani sekretów.
- Błędny filtr może uwzględnić usunięty wpis w sumie. Testy list, szczegółów i agregatów muszą potwierdzić wspólną regułę `deleted_at IS NULL`.

## Related

- **Stories**: 001-record-income, 002-select-dictionary-source.
- **Standards**: `memory-bank/standards/coding-standards.md`.
- **Previous ADRs**: ADR-004, ADR-005.
