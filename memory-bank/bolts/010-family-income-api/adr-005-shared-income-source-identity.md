---
bolt: 010-family-income-api
created: 2026-09-23T21:25:04Z
status: accepted
superseded_by: null
---

# ADR-005: Wspólna tożsamość źródła dochodu dla umów i innych źródeł

## Context

Fundament przechowuje `IncomeSource` z trwałym UUID, historią zmian i istniejącym API. Nowy zakres wymaga umów z firmą, typem, stanowiskiem i kwotą brutto oraz innych źródeł z opcjonalną podpowiedzią miesięczną. Przyszła karta miesiąca ma wybierać źródło bez rozróżniania dwóch niezależnych systemów identyfikatorów. Migracja musi zachować stare UUID i audyt; stare rekordy nie mogą automatycznie stać się umowami ani przychodami miesięcznymi.

## Decision

`IncomeSource` pozostaje wspólną, trwałą tożsamością źródła i otrzymuje jawny `kind` (`other` albo `contract`). Umowa jest źródłem rodzaju `contract` z dokładnie jednym rekordem szczegółów `Contract` powiązanym 1:1. `Company` pozostaje osobnym słownikiem gospodarstwa. Źródło `other` nie ma szczegółów umowy; jego opcjonalna miesięczna kwota jest podpowiedzią. Kwota brutto umowy jest wyłącznie polem `Contract` wraz z podstawą i nigdy nie jest kopiowana do podpowiedzi źródła.

Migracja oznacza każde istniejące źródło jako `other`, bez odgadywania rodzaju z nazwy lub kategorii. Jawna konwersja zmienia rodzaj tego samego źródła i tworzy komplet szczegółów umowy w jednej transakcji z audytem. UUID źródła nie zmienia się. Żadna z tych operacji nie tworzy przychodu miesięcznego.

## Rationale

Wspólny UUID zachowuje obecne odwołania i pozwala przyszłemu modułowi miesiąca użyć jednej listy źródeł. Osobny `Contract` ogranicza pola umowy do jej rodzaju, a jednocześnie pozwala utrzymać obecne pola innych źródeł i zgodność przejściową starego API. Granica transakcji zapobiega trwałemu stanowi `contract` bez szczegółów; audyt zachowuje znaczenie danych sprzed jawnej konwersji.

### Alternatives Considered

1. **Niezależne encje źródła i umowy z osobnymi identyfikatorami**: prostsze tabele, lecz przyszła lista wyboru potrzebowałaby dwóch przestrzeni identyfikatorów, a jawna konwersja nie zachowałaby naturalnie starego UUID.
2. **Wszystkie pola umowy w `IncomeSource`**: jedna tabela, lecz większość pól byłaby pusta dla `other`, a kwota brutto łatwiej zostałaby pomylona z podpowiedzią miesięczną.
3. **Automatyczne rozpoznawanie dawnych umów po nazwie lub kategorii**: mniej działań użytkownika, lecz nie ma wiarygodnej reguły klasyfikacji i można błędnie zmienić znaczenie starych danych.

## Consequences

### Positive

- Istniejące identyfikatory, audyt i odczyt dawnych źródeł mogą zostać zachowane.
- Przyszłe przychody miesięczne mogą wskazać jedno źródło bez przeliczania kwoty brutto umowy.
- Szczegóły umowy są walidowane osobno od pól innego źródła.

### Negative

- Odczyt pełnej umowy wymaga połączenia dwóch tabel.
- Niezmiennik dokładnie jednego `Contract` dla rodzaju `contract` obejmuje dwie tabele i wymaga transakcyjnych usług oraz testów; samo ograniczenie jednego wiersza go nie wystarczy.

### Risks

- Bezpośredni zapis ORM poza usługami mógłby pozostawić niespójny rodzaj i szczegóły. Publiczne endpointy używają wyłącznie transakcyjnych usług, a testy sprawdzają wycofanie operacji i brak częściowych rekordów.
- Stary klient może nie rozumieć nowych umów. Stary endpoint zachowuje dotychczasowy kontrakt dla rekordów `other`, dodaje jawny `kind`, a interfejs umów korzysta z osobnego endpointu.

## Related

- **Stories**: 001-company-dictionary, 002-contract-sources, 003-other-sources, 004-legacy-source-migration.
- **Standards**: coding-standards.md (kwoty dziesiętne i operacje transakcyjne), system-architecture.md (modularny monolit).
- **Previous ADRs**: ADR-002 (zakres gospodarstwa), ADR-004 (audyt zmian finansowych).
